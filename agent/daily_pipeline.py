import sys
import os
import pandas as pd
from datetime import date

# Allows importing from scraper/ and model/
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scraper"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))

from match_score import calculate_match_score #, clean_technologies
from notifier import send_message_telegram

# --- Your profile (adjust to your real values) ---
TECHNOLOGIES = ["Python", "SQL", "Tableau", "AWS", "Docker", "Pandas", "PyTorch", "BI", "TensorFlow"]
PREFERRED_ROLE = "analyst"
PREFERRED_DISTRICTS = ["Seoul", "Gangnam", "Pangyo", "Seongsu"]
MINIMUM_SALARY = 30000000  # 30 million KRW
MATCH_THRESHOLD = 50

def run_pipeline():
    df = pd.read_csv("data/processed/processed_offers.csv")

    df["match_score"] = df.apply(
        lambda row: calculate_match_score(
            row, TECHNOLOGIES, PREFERRED_ROLE, PREFERRED_DISTRICTS, MINIMUM_SALARY
        ),
        axis=1
    )

    df_sorted = df.sort_values("match_score", ascending=False)
    top_offers = df_sorted[df_sorted["match_score"] >= MATCH_THRESHOLD]

    # Save history with date, to not lose the record of what was sent each day
    top_offers.to_csv(f"data/processed/alerts_{date.today()}.csv", index=False)

    return df_sorted, top_offers

def construct_message(df_sorted, top_offers):
    if top_offers.empty:
        # No offers reached the threshold: show the top 5 anyway,
        # marked with 🟠 to make clear they're below the expected minimum
        fallback = df_sorted.head(5)
        lines = [
            f"*Daily summary — {date.today()}*",
            f"THRESHOLD = {MATCH_THRESHOLD}%",
            "",
            "No offers reached the match threshold. Showing top 5 anyway:",
            ""
        ]
        for _, row in fallback.iterrows():
            lines.append(f"🟠 *{row['company']}* — {row.get('role_title', 'N/D')} — {row.get('link', 'N/D')} — Match: {row['match_score']}%")
        return "\n".join(lines)

    lines = [
        f"*Daily summary — {date.today()}*",
        f"THRESHOLD = {MATCH_THRESHOLD}%",
        ""
    ]
    for _, row in top_offers.head(10).iterrows():
        lines.append(f"🟢 *{row['company']}* — {row.get('role_title', 'N/D')} — {row.get('link', 'N/D')} — Match: {row['match_score']}%")
    return "\n".join(lines)

if __name__ == "__main__":
    df_sorted, top_offers = run_pipeline()
    message = construct_message(df_sorted, top_offers)
    sent = send_message_telegram(message)
    print("Notification sended:", sent)
    print(f"Offers with high match score found: {len(top_offers)}")