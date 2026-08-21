import json
import logging
import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
CAREERJET_API_KEY = os.getenv("CAREERJET_API_KEY")
PUBLIC_IP = os.getenv("PUBLIC_IP")

CAREERJET_JSON_PATH = os.path.join("docs", "data", "careerjet_offers.json")

logger = logging.getLogger(__name__)


def fetch_careerjet_offers(keywords, location="Seoul"):
    url = "http://public.api.careerjet.net/search"
    params = {
        "keywords": keywords,
        "location": location,
        "affid": CAREERJET_API_KEY,
        "user_ip": PUBLIC_IP,
        "url": "https://www.jobtrackerkorea.dev",
        "user_agent": "Mozilla/5.0",
        "locale_code": "ko_KR",
        "pagesize": 20
    }
    headers = {
        "Referer": "https://www.jobtrackerkorea.dev"
    }
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json().get("jobs", [])

def offers_to_dataframe(offers):
    rows = []
    today_str = datetime.today().strftime("%Y-%m-%d")
    for o in offers:
        rows.append({
            "company": o.get("company", "N/D"),
            "title": o.get("title", "N/D"),
            "location": o.get("locations", "N/D"),
            "description": o.get("description", "N/D"),
            "link": o.get("url", "N/D"),
            "source": "Careerjet",
            "date_posted": o.get("date", "N/D"),
            "date_tracked": today_str
        })
    return pd.DataFrame(rows)

def is_korean_job(row):
    text = " ".join([
        str(row.get("location", "")),
        str(row.get("title", "")),
        str(row.get("description", ""))
    ]).lower()

    palabras_clave = ["korea", "seoul", "pangyo", "gangnam", "incheon", "busan"]

    return any(p in text for p in palabras_clave)


def load_history_json():
    """Carga el histórico de Careerjet desde su JSON en /docs. Tolerante a fichero corrupto."""
    if not os.path.exists(CAREERJET_JSON_PATH):
        return pd.DataFrame()
    try:
        with open(CAREERJET_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data.get("offers", []) if isinstance(data, dict) else data
        return pd.DataFrame(records)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Careerjet: histórico JSON ilegible (%s). Se empieza de cero.", exc)
        return pd.DataFrame()


def save_history_json(df_combined):
    os.makedirs(os.path.dirname(CAREERJET_JSON_PATH), exist_ok=True)
    payload = {
        "updated_at": datetime.now().isoformat(),
        "total_offers": len(df_combined),
        "offers": df_combined.to_dict(orient="records"),
    }
    with open(CAREERJET_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def collect_new_offers(keywords_list):
    """
    Scrapea Careerjet, persiste el histórico en JSON dentro de /docs
    (docs/data/careerjet_offers.json) y devuelve SOLO las ofertas nuevas de hoy.
    """
    all_dfs = [offers_to_dataframe(fetch_careerjet_offers(kw)) for kw in keywords_list]
    df_new = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

    if df_new.empty:
        logger.warning("Careerjet: 0 ofertas recibidas de la API.")
        return pd.DataFrame()

    df_new = df_new[df_new.apply(is_korean_job, axis=1)]
    logger.info("Careerjet: %d ofertas tras filtro de localización.", len(df_new))

    df_existing = load_history_json()
    existing_links = set(df_existing.get("link", pd.Series(dtype=str)).dropna())

    df_only_new = df_new[~df_new["link"].isin(existing_links)].copy()

    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset="link", keep="last")
    save_history_json(df_combined)

    logger.info(
        "Careerjet: %d nuevas de hoy | histórico JSON (/docs): %d ofertas.",
        len(df_only_new), len(df_combined),
    )
    return df_only_new
