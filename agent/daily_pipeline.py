import ast
import sys
import os
import pandas as pd
from datetime import date

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scraper"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))

from jooble_connector import collect_new_offers
from llm_judge import evaluate_offer
from notifier import send_message_telegram

MATCH_THRESHOLD = 50

KEYWORDS = [
    "data analyst",
    "data scientist",
    "ai engineer",
    "data analyst visa sponsorship",
    "data scientist visa sponsorship",
    "ai engineer visa sponsorship",
    "data analyst E-7 visa",
    "data scientist E-7 visa",
    "ai engineer E-7 visa",
    "korea relocation"
]


def compute_match_score(row):
    score = 0

    techs = row.get("technologies_found", [])
    if isinstance(techs, str):
        try:
            techs = ast.literal_eval(techs)
        except:
            techs = []

    score += min(len(techs) * 5, 35)

    try:
        score += float(row.get("visa_sponsorship_likelihood", 0)) * 0.3
    except:
        pass

    if row.get("role_category") in ["analyst", "scientist", "ai_engineer"]:
        score += 20

    if "korea" in str(row.get("location", "")).lower():
        score += 10

    if row.get("salary_meets_minimum") is True:
        score += 5

    return max(0, int(score))


def quick_filter(row):
    try:
        text = f"{row.get('title','')} {row.get('description','')}".lower()
        keywords = ["data", "python", "sql", "machine learning", "ai"]
        return any(k in text for k in keywords)
    except:
        return False


def load_profile():
    with open("data/profile/cv.txt", "r", encoding="utf-8") as f:
        return f.read()


def run_pipeline():

    df = collect_new_offers(KEYWORDS)

    if df.empty or "link" not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    df = df.fillna("N/D")

    today_str = date.today().strftime("%Y-%m-%d")

    if "date_tracked" in df.columns:
        df = df[df["date_tracked"] == today_str]

    df = df[df.apply(quick_filter, axis=1)]

    processed_path = "data/processed/processed_offers.csv"

    if os.path.exists(processed_path) and os.path.getsize(processed_path) > 0:
        df_procesado_previo = pd.read_csv(processed_path)
        links_ya_evaluados = set(df_procesado_previo.get("link", []).dropna())
    else:
        df_procesado_previo = pd.DataFrame()
        links_ya_evaluados = set()

    df_nuevas = df[~df["link"].isin(links_ya_evaluados)].copy()

    print(f"\n📊 {len(df)} offers today | 🆕 {len(df_nuevas)} new\n")

    if df_nuevas.empty:
        print("No new offers to evaluate.")
        df_final = df_procesado_previo
    else:
        profile = load_profile()
        resultados = []

        for i, (_, row) in enumerate(df_nuevas.iterrows(), start=1):
            print("\n" + "=" * 60)
            print(f"🔎 Evaluating {i}/{len(df_nuevas)}")
            print(f"🏢 {row.get('company','N/D')}")
            print(f"💼 {row.get('title','N/D')}")
            print(f"🌍 {row.get('location','N/D')}")
            print(f"🔗 {row.get('link','N/D')}")
            print("-" * 60)

            resultado = evaluate_offer(row, profile)

            match_score = resultado.get("match_score", "N/D")
            visa_score = resultado.get("visa_sponsorship_likelihood", "N/D")

            print(f"✅ Match: {match_score}%")
            print(f"🛂 Visa: {visa_score}%")
            print(f"🧠 {resultado.get('reasoning','')}")
            print("=" * 60)

            resultados.append(resultado)

        eval_df = pd.json_normalize(resultados)

        df_nuevas_evaluadas = pd.concat(
            [df_nuevas.reset_index(drop=True), eval_df.reset_index(drop=True)],
            axis=1
        )

        df_nuevas_evaluadas["match_score"] = df_nuevas_evaluadas.apply(
            compute_match_score, axis=1
        )

        df_final = pd.concat(
            [df_procesado_previo, df_nuevas_evaluadas],
            ignore_index=True
        )

        df_final = df_final.drop_duplicates(subset="link", keep="last")

    if not df_final.empty:
        df_final.to_csv(processed_path, index=False)

    df_final = df_final.fillna("N/D")

    if "match_score" not in df_final.columns:
        df_final["match_score"] = 0

    df_sorted = df_final.sort_values("match_score", ascending=False)

    top_offers = df_sorted[df_sorted["match_score"] >= MATCH_THRESHOLD]

    if not top_offers.empty:
        top_offers.to_csv(f"data/processed/alerts_{date.today()}.csv", index=False)

    print(f"\n🏁 Done → {len(top_offers)} offers above threshold\n")

    return df_sorted, top_offers


def construct_message(df_sorted, top_offers):

    if top_offers.empty:
        fallback = df_sorted.head(5)

        lines = [
            f"*Daily summary — {date.today()}*",
            f"THRESHOLD = {MATCH_THRESHOLD}%",
            "",
            "No offers reached the match threshold. Showing top 5 anyway:",
            ""
        ]

        for _, row in fallback.iterrows():
            lines.append(
                f"🟠 *{row.get('company','N/D')}* — {row.get('title','N/D')} — {row.get('link','N/D')} — Match: {row.get('match_score','N/D')}%"
            )

        return "\n".join(lines)

    lines = [
        f"*Daily summary — {date.today()}*",
        f"THRESHOLD = {MATCH_THRESHOLD}%",
        ""
    ]

    for _, row in top_offers.head(10).iterrows():
        lines.append(
            f"🟢 *{row.get('company','N/D')}* — {row.get('title','N/D')}\n"
            f"{row.get('link','N/D')}\n"
            f"Match: {row.get('match_score','N/D')}% | Visa: {row.get('visa_sponsorship_likelihood','N/D')}%\n"
            f"_{row.get('reasoning','')}_\n"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    df_sorted, top_offers = run_pipeline()
    message = construct_message(df_sorted, top_offers)
    send_message_telegram(message)