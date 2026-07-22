import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("JOOBLE_API_KEY")


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
            "date_tracked": today_str  # 🔥 NUEVO CAMPO
        })

    return pd.DataFrame(rows)


def is_korean_location(location_text):
    if pd.isna(location_text):
        return False
    palabras_clave = ["korea", "seoul", "pangyo", "gangnam", "incheon", "busan"]
    return any(p in str(location_text).lower() for p in palabras_clave)


def collect_new_offers(keywords_list):
    all_dfs = [offers_to_dataframe(fetch_jooble_offers(kw)) for kw in keywords_list]
    df_new = pd.concat(all_dfs, ignore_index=True)

    if df_new.empty:
        print("WARNING: Jooble returned 0 offers.")
        if os.path.exists("data/raw/offers.csv"):
            return pd.read_csv("data/raw/offers.csv")
        return pd.DataFrame()

    df_new = df_new[df_new["location"].apply(is_korean_location)]

    df_existing = pd.read_csv("data/raw/offers.csv") if os.path.exists("data/raw/offers.csv") else pd.DataFrame()

    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset="link", keep="last")

    df_combined.to_csv("data/raw/offers.csv", index=False)

    return df_combined