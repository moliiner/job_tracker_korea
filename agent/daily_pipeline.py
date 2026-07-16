import sys
import os
import pandas as pd
from datetime import date

# Permite importar desde scraper/ y model/
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scraper"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))

from match_score import calculate_match_score #, clean_technologies
from notifier import send_message_telegram

# --- Your profile (adjust to your real values) ---
TECHNOLOGIES = ["Python", "SQL", "Tableau", "AWS"]
PREFERRED_ROLE = "analyst"
PREFERRED_DISTRICTS = ["Gangnam", "Pangyo", "Seongsu"]
MINIMUM_SALARY = 30000000  # 30 million KRW
MATCH_THRESHOLD = 60

def run_pipeline():
    df = pd.read_csv("data/processed/processed_offers.csv")

    df["match_score"] = df.apply(
        lambda row: calculate_match_score(
            row, TECHNOLOGIES, PREFERRED_ROLE, PREFERRED_DISTRICTS, MINIMUM_SALARY
        ),
        axis=1
    )

    top_offers = df[df["match_score"] >= MATCH_THRESHOLD].sort_values("match_score", ascending=False)

    # Save history with date, to not lose the record of what was sent each day
    top_offers.to_csv(f"data/processed/alerts_{date.today()}.csv", index=False)

    return top_offers

def construct_message(top_offers):
    if top_offers.empty:
        return "No offers found with high match score. 🔍"

    lines = [f"*Daily summary — {date.today()}*", ""]
    for _, row in top_offers.head(10).iterrows():
        lines.append(f"🟢 *{row['company']}* — {row.get('title', 'N/D')} — Match: {row['match_score']}%")
    return "\n".join(lines)

if __name__ == "__main__":
    top_offers = run_pipeline()
    message = construct_message(top_offers)
    sent = send_message_telegram(message)
    print("Notification sended:", sent)
    print(f"Offers with high match score found: {len(top_offers)}")