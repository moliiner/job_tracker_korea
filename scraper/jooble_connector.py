import logging
import os

import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("JOOBLE_API_KEY")

RAW_OFFERS_CSV = os.path.join("data", "raw", "offers.csv")

logger = logging.getLogger(__name__)


def fetch_jooble_offers(keywords, location="Seoul, South Korea"):
    url = f"https://jooble.org/api/{API_KEY}"
    payload = {"keywords": keywords, "location": location, "radius": "40"}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("jobs", [])


def offers_to_dataframe(offers):
    rows = []
    today_str = datetime.today().strftime("%Y-%m-%d")

    for o in offers:
        rows.append({
            "company": o.get("company", "N/D"),
            "title": o.get("title", "N/D"),
            "location": o.get("location", "N/D"),
            "description": o.get("snippet", "N/D"),
            "link": o.get("link", "N/D"),
            "source": "Jooble",
            "date_posted": o.get("updated", "N/D"),
            "date_tracked": today_str
        })

    return pd.DataFrame(rows)


def is_korean_location(location_text):
    if pd.isna(location_text):
        return False
    palabras_clave = ["korea", "seoul", "pangyo", "gangnam", "incheon", "busan"]
    return any(p in str(location_text).lower() for p in palabras_clave)


def collect_new_offers(keywords_list):
    """
    Scrapea Jooble, persiste el histórico en CSV (data/raw/offers.csv) y
    devuelve SOLO las ofertas nuevas de hoy (las que no estaban en el histórico).
    """
    all_dfs = [offers_to_dataframe(fetch_jooble_offers(kw)) for kw in keywords_list]
    df_new = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

    if df_new.empty:
        logger.warning("Jooble: 0 ofertas recibidas de la API.")
        return pd.DataFrame()

    df_new = df_new[df_new["location"].apply(is_korean_location)]
    logger.info("Jooble: %d ofertas tras filtro de localización.", len(df_new))

    df_existing = pd.read_csv(RAW_OFFERS_CSV) if os.path.exists(RAW_OFFERS_CSV) else pd.DataFrame()
    existing_links = set(df_existing.get("link", pd.Series(dtype=str)).dropna())

    df_only_new = df_new[~df_new["link"].isin(existing_links)].copy()

    os.makedirs(os.path.dirname(RAW_OFFERS_CSV), exist_ok=True)

    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset="link", keep="last")
    df_combined.to_csv(RAW_OFFERS_CSV, index=False)

    logger.info(
        "Jooble: %d nuevas de hoy | histórico CSV: %d ofertas.",
        len(df_only_new), len(df_combined),
    )
    return df_only_new
