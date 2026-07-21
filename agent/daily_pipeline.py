import sys
import os
import pandas as pd
from datetime import date

# Añadir la ruta del proyecto al PYTHONPATH para que las imports absolutas funcionen
# Esto permite hacer from scraper... en lugar de importar módulos locales directamente si no están en el mismo nivel
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scraper.jooble_connector import collect_new_offers
from model.llm_judge import evaluate_offer
from agent.notifier import send_message_telegram  # Asumiendo que notifier está en agent también o se importa relativo

MATCH_THRESHOLD = 60
KEYWORDS = [
    "data analyst Seoul",
    "data scientist Korea",
    "AI engineer Seoul",
    "data analyst visa sponsorship",
    "AI engineer Korea relocation"
]

def load_profile():
    # Usar ruta absoluta basada en el directorio del script para asegurar que encuentra el CV aunque se cambie el cwd
    cv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "profile", "cv.txt")
    if not os.path.exists(cv_path):
        raise FileNotFoundError(f"CV file not found at {cv_path}")
        
    with open(cv_path, "r", encoding="utf-8") as f:
        return f.read()

def run_pipeline():
    df = collect_new_offers(KEYWORDS)

    # Evaluate every offer with the LLM (classification + scoring in one call)
    try:
        profile = load_profile()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

    evaluations = df.apply(lambda row: evaluate_offer(row, profile), axis=1)
    eval_df = pd.json_normalize(evaluations)

    df_final = pd.concat([df.reset_index(drop=True), eval_df.reset_index(drop=True)], axis=1)

    # delete errors LLM
    df_final = df_final[df_final["match_score"].notna()]
    df_final = df_final[df_final["match_score"] > 0]

    df_sorted = df_final.sort_values("match_score", ascending=False)
    top_offers = df_sorted[df_sorted["match_score"] >= MATCH_THRESHOLD]

    # Guardar con rutas relativas a la raíz del proyecto (asumiendo que se ejecuta desde ahí)
    os.makedirs("data/processed", exist_ok=True)
    
    df_final.to_csv("data/processed/processed_offers.csv", index=False)
    top_offers.to_csv(f"data/processed/alerts_{date.today()}.csv", index=False)

    return df_sorted, top_offers

def construct_message(df_sorted, top_offers):
    lines = [] #Initialize the lines list to store the message content
    
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

    # Determine how many offers to show based on the requested condition
    # If it exceeds the threshold (more than 5 results), we show only 5.
    # If there are <= 5, we show all (which are already sorted by match_score).
    num_to_show = 5 if len(top_offers) > 5 else len(top_offers)

    lines = [
        f"*Daily summary — {date.today()}*",
        f"Found {len(top_offers)} offers above threshold:",
        ""
    ]
    
    # Use num_to_show instead of head(10) or iterate over top_offers directly
    for _, row in top_offers.head(num_to_show).iterrows():
        lines.append(f"🟢 *{row['company']}* — {row.get('title', 'N/D')}\n"
                     f"{row.get('link', 'N/D')}\n"
                     f"Match: {row['match_score']}% | Visa: {row['visa_sponsorship_likelihood']}%\n"
                     f"_{row['reasoning']}_\n")
    
    return "\n".join(lines)

if __name__ == "__main__":
    df_sorted, top_offers = run_pipeline()
    
    if not top_offers.empty or not df_sorted.empty:
        message = construct_message(df_sorted, top_offers)
        # Adjust import if notifier is in agent
        try:
            from agent.notifier import send_message_telegram
            sent = send_message_telegram(message)
            print("Notification sent:", sent)
        except ImportError:
            print("Notifier not found or not configured.")
            
        print(f"Offers with high match score found: {len(top_offers)}")
    else:
        print("No offers processed.")