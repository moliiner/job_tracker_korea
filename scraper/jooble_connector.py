import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JOOBLE_API_KEY")

def fetch_jooble_offers(keywords, location="Seoul"):
    url = f"https://jooble.org/api/{API_KEY}"
    payload = {"keywords": keywords, "location": location}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("jobs", [])

def offers_to_dataframe(offers):
    rows = []
    for o in offers:
        rows.append({
            "company": o.get("company", ""),
            "title": o.get("title", ""),
            "location": o.get("location", ""),
            "description": o.get("snippet", ""),
            "link": o.get("link", ""),
            "source": "Jooble"
        })
    return pd.DataFrame(rows)

def collect_new_offers(keywords_list):
    all_dfs = [offers_to_dataframe(fetch_jooble_offers(kw)) for kw in keywords_list]
    df_new = pd.concat(all_dfs, ignore_index=True)

    df_existing = pd.read_csv("data/raw/offers.csv") if os.path.exists("data/raw/offers.csv") else pd.DataFrame()
    df_combined = pd.concat([df_existing, df_new], ignore_index=True).drop_duplicates(subset="link", keep="first")
    df_combined.to_csv("data/raw/offers.csv", index=False)
    return df_combined