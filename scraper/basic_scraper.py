import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.text, "html.parser")

df = pd.read_csv("data/raw/offers.csv")

df["mentions_visa"] = df["description"].str.contains(
    "visa sponsorship|E-7|foreigner", case=False, na=False
)

TECH_PATTERN = r"(Python|SQL|AWS|Docker|Tableau|BI|Pandas|PyTorch|TensorFlow)"

def track_unique_technologies(description):
    if pd.isna(description):
        return ""
    # re.IGNORECASE avoide that "python" and "Python" count as different things
    finded = re.findall(TECH_PATTERN, description, flags=re.IGNORECASE)
    # set() delete duplicated: each techonolgy count 1 single time per offer,
    # no matter how many times the word appears in the text
    unique = sorted(set(t.capitalize() for t in finded))
    return ", ".join(unique)  # saved as text, not as a Python list

df["technologies"] = df["description"].apply(track_unique_technologies)

df.to_csv("data/processed/processed_offers.csv", index=False)

