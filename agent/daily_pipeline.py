import ast
import sys
import os
import logging
import pandas as pd
import json
from datetime import date, datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scraper"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))

from jooble_connector import collect_new_offers as collect_jooble_offers
from careerjet_connector import collect_new_offers as collect_careerjet_offers

from llm_judge import evaluate_offer
from notifier import send_message_telegram

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 50

PROCESSED_OFFERS_CSV = os.path.join("data", "processed", "processed_offers.csv")

COMMON_COLUMNS = [
    "company",
    "title",
    "location",
    "description",
    "link",
    "source",
    "date_posted",
    "date_tracked",
]

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

def export_web_json(df_today_sorted, top_offers):
    output_path = "docs/data/offers.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    def offer_to_dict(row):
        return {
            "company": row.get("company", "N/D"),
            "title": row.get("title", "N/D"),
            "link": row.get("link", "N/D"),
            "source": row.get("source", "N/D"),
            "match_score": int(row.get("match_score", 0)),
            "visa_likelihood": row.get("visa_sponsorship_likelihood", "N/D"),
            "role_category": row.get("role_category", "N/D"),
            "reasoning": row.get("reasoning", ""),
        }

    payload = {
        "generated_at": datetime.now().isoformat(),
        "threshold": MATCH_THRESHOLD,
        "top_offers": [offer_to_dict(r) for _, r in top_offers.head(10).iterrows()],
        "today_all": [offer_to_dict(r) for _, r in df_today_sorted.head(20).iterrows()],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


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

    # --- Studies (10 points) ---
    education_match = row.get("education_match")
    if education_match is True or education_match == "unknown":
        # "unknown" counts as neutral-positive: the offer doesn't rule out your profile
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


def unify_offers(df_jooble, df_careerjet):
    """
    Normaliza ambas fuentes a un esquema común (con campo `source`) y las une
    en un único DataFrame en memoria. Estructura única para guardado, web y Telegram.
    """
    frames = []
    for df in (df_jooble, df_careerjet):
        if df is None or df.empty:
            continue
        frames.append(df.reindex(columns=COMMON_COLUMNS))

    if not frames:
        return pd.DataFrame(columns=COMMON_COLUMNS)

    return pd.concat(frames, ignore_index=True)


def log_counts_per_source(df, stage):
    if df.empty or "source" not in df.columns:
        logger.info("[%s] 0 ofertas.", stage)
        return
    counts = ", ".join(f"{src}: {n}" for src, n in df["source"].value_counts().items())
    logger.info("[%s] %d ofertas (%s)", stage, len(df), counts)


def run_pipeline():
    logger.info("Starting pipeline...")

    # --- 1. Recolección (cada conector persiste su histórico y devuelve SOLO ofertas nuevas de hoy) ---
    df_jooble = collect_jooble_offers(KEYWORDS)
    df_careerjet = collect_careerjet_offers(KEYWORDS)

    df = unify_offers(df_jooble, df_careerjet)
    log_counts_per_source(df, "Recolectadas hoy")

    # --- 2. Limpieza básica y normalización de fechas ---
    # IMPORTANTE: normalizar fechas ANTES del fillna para no convertir fechas ausentes en "N/D"
    if df.empty or "date_tracked" not in df.columns:
        logger.warning("No offers collected today from any source.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df["date_tracked"] = pd.to_datetime(df["date_tracked"], errors="coerce").dt.date
    today = date.today()

    # --- 3. Filtrar SOLO hoy ---
    df_today = df[df["date_tracked"] == today].copy()
    log_counts_per_source(df_today, "Con fecha de hoy")

    # --- 4. Filtro rápido de keywords ---
    df_today = df_today[df_today.apply(quick_filter, axis=1)]
    log_counts_per_source(df_today, "Tras filtro rápido")

    # --- 5. Cargar histórico procesado (dedupe global por link entre fuentes) ---
    if os.path.exists(PROCESSED_OFFERS_CSV) and os.path.getsize(PROCESSED_OFFERS_CSV) > 0:
        df_procesado_previo = pd.read_csv(PROCESSED_OFFERS_CSV)

        if "date_tracked" in df_procesado_previo.columns:
            df_procesado_previo["date_tracked"] = pd.to_datetime(
                df_procesado_previo["date_tracked"], errors="coerce"
            ).dt.date

        links_ya_evaluados = set(df_procesado_previo.get("link", []).dropna())
    else:
        df_procesado_previo = pd.DataFrame()
        links_ya_evaluados = set()

    # --- 6. Detectar nuevas (no duplicadas contra el histórico global) ---
    df_nuevas = df_today[~df_today["link"].isin(links_ya_evaluados)].copy()
    log_counts_per_source(df_nuevas, "Nuevas a evaluar")

    # --- 7. Evaluación ---
    if df_nuevas.empty:
        logger.info("No new offers to evaluate.")
        df_final = df_procesado_previo

    else:
        profile = load_profile()
        resultados = []

        for i, (_, row) in enumerate(df_nuevas.iterrows(), start=1):
            resultado = evaluate_offer(row, profile)
            logger.info(
                "[%d/%d] [%s] %s — %s%%",
                i, len(df_nuevas), row.get("source", "N/D"),
                row.get("company", "N/D"), resultado.get("match_score"),
            )
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

        # Deduplicación robusta por link
        df_final = df_final.drop_duplicates(subset="link", keep="last")

    # --- 8. Guardado (histórico procesado común, lo consume dashboard/app.py) ---
    if not df_final.empty:
        df_final.to_csv(PROCESSED_OFFERS_CSV, index=False)

    df_final = df_final.fillna("N/D")

    if "match_score" not in df_final.columns:
        df_final["match_score"] = 0

    # --- 9. Outputs ---
    df_all_sorted = df_final.sort_values("match_score", ascending=False)

    df_today_final = df_final[df_final["date_tracked"] == today]
    df_today_sorted = df_today_final.sort_values("match_score", ascending=False)

    top_offers = df_today_sorted[
        df_today_sorted["match_score"] >= MATCH_THRESHOLD
    ]

    if not top_offers.empty:
        top_offers.to_csv(
            f"data/processed/alerts_{today}.csv",
            index=False
        )

    logger.info("Done -> %d offers above threshold today.", len(top_offers))
    log_counts_per_source(top_offers, "Sobre el umbral hoy")

    return df_today_sorted, top_offers, df_all_sorted


def _source_counts(df):
    """Resumen 'Fuente: N' a partir de la columna source (vacío si no aplica)."""
    if df is None or df.empty or "source" not in df.columns:
        return "Jooble: 0 | Careerjet: 0"
    counts = df["source"].value_counts()
    return f"Jooble: {int(counts.get('Jooble', 0))} | Careerjet: {int(counts.get('Careerjet', 0))}"


def construct_message(df_today_sorted, top_offers, df_all_sorted):

    header = [
        f"*Daily summary — {date.today()}*",
        f"THRESHOLD = {MATCH_THRESHOLD}%",
        f"New today -> {_source_counts(df_today_sorted)}",
        "",
    ]

    # Caso 1: hay ofertas de hoy que superan el umbral
    if not top_offers.empty:
        lines = header
        for _, row in top_offers.head(10).iterrows():
            lines.append(
                f"🟢 *{row.get('company','N/D')}* — {row.get('title','N/D')} [{row.get('source','N/D')}]\n"
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
                f"🟠 [{row.get('source','N/D')}] *{row.get('company','N/D')}* — {row.get('title','N/D')} — {row.get('link','N/D')} — Match: {row.get('match_score','N/D')}%"
            )
        return "\n".join(lines)

    # Caso 3: no se evaluó NINGUNA oferta nueva hoy (todas ya estaban vistas en ninguna fuente)
    lines = header + ["No new offers were found today across any source.", "Best matches from previous days, for reference:", ""]
    for _, row in df_all_sorted.head(5).iterrows():
        lines.append(
            f"⚪ *{row.get('company','N/D')}* — {row.get('title','N/D')} — {row.get('link','N/D')} — Match: {row.get('match_score','N/D')}%"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    df_today_sorted, top_offers, df_all_sorted = run_pipeline()

    export_web_json(df_today_sorted, top_offers)
    logger.info("Web JSON exported to docs/data/offers.json")

    message = construct_message(df_today_sorted, top_offers, df_all_sorted)

    sent_ok = send_message_telegram(message)
    if sent_ok:
        logger.info("Telegram notification sent successfully.")
    else:
        logger.error("Telegram notification FAILED (check notifier logs).")