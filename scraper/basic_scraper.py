import requests 
from bs4 import BeautifulSoup
import pandas as pd

def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.text, "html.parser")

df = pd.read_csv("data/raw/offers.csv")

df["mentions_visa"] = df["description"].str.contains("visa sponsorship|E-7|foreigner", case=False, na=False)
df["technologies"] = df["description"].str.extractall(r"(Python|SQL|AWS|Docker|Tableau|BI|Pandas|PyTorch|TensorFlow)").groupby(level=0)[0].apply(list)

df.to_csv("data/processed/processed_offers.csv", index=False)