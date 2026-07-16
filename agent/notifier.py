import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_message_telegram(mensaje):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, data={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})
    return response.status_code == 200