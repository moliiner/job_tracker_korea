import sys
import os
import pandas as pd
from datetime import date

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scraper"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))

from jooble_connector import collect_new_offers
from llm_judge import evaluate_offer
from notifier import send_message_telegram

MATCH_THRESHOLD = 40
KEYWORDS = [
    "data analyst Seoul",
    "data scientist Korea",
    "AI engineer Seoul",
    "data analyst visa sponsorship",
    "AI engineer Korea relocation"
]

def run_pipeline():
    df = collect_new_offers(KEYWORDS)

    # Evaluate every offer with the LLM (classification + scoring in one call)
    evaluations = df.apply(evaluate_offer, axis=1)
    eval_df = pd.json_normalize(evaluations)

    df_final = pd.concat([df.reset_index(drop=True), eval_df.reset_index(drop=True)], axis=1)

    df_sorted = df_final.sort_values("match_score", ascending=False)
    top_offers = df_sorted[df_sorted["match_score"] >= MATCH_THRESHOLD]

    df_final.to_csv("data/processed/processed_offers.csv", index=False)
    top_offers.to_csv(f"data/processed/alerts_{date.today()}.csv", index=False)

    return df_sorted, top_offers

def construct_message(df_sorted, top_offers):
    if top_offers.empty:
        fallback = df_sorted.head(5)
        lines = [
            f"*Daily summary — {date.today()}*",
            f"THRESHOLD = {MATCH_THRESHOLD}%",
            "",
            "No offers reached the match threshold. Showing top 5 anyway:",
            ""
        ]
        for _, row in fallback.iterrows():
            lines.append(f"🟠 *{row['company']}* — {row.get('title', 'N/D')} — {row.get('link', 'N/D')} — Match: {row['match_score']}%")
        return "\n".join(lines)

    lines = [f"*Daily summary — {date.today()}*", f"THRESHOLD = {MATCH_THRESHOLD}%", ""]
    for _, row in top_offers.head(10).iterrows():
        lines.append(f"🟢 *{row['company']}* — {row.get('title', 'N/D')} — {row.get('link', 'N/D')} — Match: {row['match_score']}%")
    return "\n".join(lines)

if __name__ == "__main__":
    df_sorted, top_offers = run_pipeline()
    message = construct_message(df_sorted, top_offers)
    sent = send_message_telegram(message)
    print("Notification sended:", sent)
    print(f"Offers with high match score found: {len(top_offers)}")