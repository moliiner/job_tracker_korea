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

    # --- Technologies (25 points) ---
    techs = row.get("technologies_found", [])
    if isinstance(techs, str):
        try:
            techs = ast.literal_eval(techs)
        except:
            techs = []
    score += min(len(techs) * 5, 25)

    # --- Probability of Visa Sponsorship (25 points) ---
    try:
        score += float(row.get("visa_sponsorship_likelihood", 0)) * 0.25
    except:
        pass

    # --- Role Category (15 points) ---
    if row.get("role_category") in ["analyst", "scientist", "ai_engineer"]:
        score += 15

    # --- Location (10 points) ---
    if "korea" in str(row.get("location", "")).lower():
        score += 10

    # --- Minimum Salary (5 points) ---
    if row.get("salary_meets_minimum") is True:
        score += 5

    # --- Studies (10 puntos) ---
    education_match = row.get("education_match")
    if education_match is True or education_match == "unknown":
        # "unknown" cuenta como neutro-positivo: la oferta no descarta tu perfil
        score += 10

    # --- Languages (10 points) ---
    languages = row.get("languages_required", [])
    if isinstance(languages, str):
        try:
            languages = ast.literal_eval(languages)
        except:
            languages = []
    languages_lower = [str(l).lower() for l in languages]

    if "english" in languages_lower:
        score += 5
    if "spanish" in languages_lower or "español" in languages_lower:
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
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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
            resultado = evaluate_offer(row, profile)
            print(f"[{i}/{len(df_nuevas)}] {row.get('company','N/D')} — {resultado.get('match_score')}%")
            resultados.append(resultado)

        eval_df = pd.json_normalize(resultados)
        df_nuevas_evaluadas = pd.concat(
            [df_nuevas.reset_index(drop=True), eval_df.reset_index(drop=True)], axis=1
        )
        df_nuevas_evaluadas["match_score"] = df_nuevas_evaluadas.apply(compute_match_score, axis=1)

        df_final = pd.concat([df_procesado_previo, df_nuevas_evaluadas], ignore_index=True)
        df_final = df_final.drop_duplicates(subset="link", keep="last")

    if not df_final.empty:
        df_final.to_csv(processed_path, index=False)

    df_final = df_final.fillna("N/D")
    if "match_score" not in df_final.columns:
        df_final["match_score"] = 0

    # --- Separamos "todo el histórico" de "solo lo de hoy" ---
    df_all_sorted = df_final.sort_values("match_score", ascending=False)

    if "date_tracked" in df_final.columns:
        df_today = df_final[df_final["date_tracked"] == today_str]
    else:
        df_today = df_final

    df_today_sorted = df_today.sort_values("match_score", ascending=False)
    top_offers = df_today_sorted[df_today_sorted["match_score"] >= MATCH_THRESHOLD]

    if not top_offers.empty:
        top_offers.to_csv(f"data/processed/alerts_{date.today()}.csv", index=False)

    print(f"\n🏁 Done → {len(top_offers)} offers above threshold today\n")

    return df_today_sorted, top_offers, df_all_sorted


def construct_message(df_today_sorted, top_offers, df_all_sorted):

    header = [f"*Daily summary — {date.today()}*", f"THRESHOLD = {MATCH_THRESHOLD}%", ""]

    # Caso 1: hay ofertas de hoy que superan el umbral
    if not top_offers.empty:
        lines = header
        for _, row in top_offers.head(10).iterrows():
            lines.append(
                f"🟢 *{row.get('company','N/D')}* — {row.get('title','N/D')}\n"
                f"{row.get('link','N/D')}\n"
                f"Match: {row.get('match_score','N/D')}% | Visa: {row.get('visa_sponsorship_likelihood','N/D')}%\n"
                f"_{row.get('reasoning','')}_\n"
            )
        return "\n".join(lines)

    # Caso 2: hubo ofertas nuevas hoy, pero ninguna superó el umbral
    if not df_today_sorted.empty:
        lines = header + ["No offers reached the match threshold today. Showing today's top 5 anyway:", ""]
        for _, row in df_today_sorted.head(5).iterrows():
            lines.append(
                f"🟠 *{row.get('company','N/D')}* — {row.get('title','N/D')} — {row.get('link','N/D')} — Match: {row.get('match_score','N/D')}%"
            )
        return "\n".join(lines)

    # Caso 3: no se evaluó NINGUNA oferta nueva hoy (todas ya estaban vistas)
    lines = header + ["No new offers were found today (all Jooble results were already tracked).", "Best matches from previous days, for reference:", ""]
    for _, row in df_all_sorted.head(5).iterrows():
        lines.append(
            f"⚪ *{row.get('company','N/D')}* — {row.get('title','N/D')} — {row.get('link','N/D')} — Match: {row.get('match_score','N/D')}%"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    df_today_sorted, top_offers, df_all_sorted = run_pipeline()
    message = construct_message(df_today_sorted, top_offers, df_all_sorted)
    send_message_telegram(message)