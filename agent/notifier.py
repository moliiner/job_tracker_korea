import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_MAX_LEN = 4096
CHUNK_SAFE_LEN = 3900


def _split_message(text, limit=CHUNK_SAFE_LEN):
    """
    Parte un mensaje en trozos <= limit respetando saltos de línea.
    Telegram rechaza mensajes de más de 4096 caracteres con HTTP 400.
    """
    if len(text) <= limit:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def send_message_telegram(mensaje):
    """
    Envía un mensaje a Telegram, partiéndolo en chunks si supera el límite.
    Si un chunk falla al parsear Markdown, se reintenta como texto plano.
    Devuelve True solo si TODOS los chunks se enviaron correctamente.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.error("Telegram: faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID. No se envía nada.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = _split_message(mensaje)

    logger.info("Telegram: enviando mensaje en %d chunk(s) (%d caracteres).", len(chunks), len(mensaje))

    all_ok = True
    for i, chunk in enumerate(chunks, start=1):
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, data=payload, timeout=30)
            if response.status_code == 200:
                logger.info("Telegram: chunk %d/%d enviado.", i, len(chunks))
                continue
            # Fallo típico: entidades Markdown sin escapar -> reintento como texto plano
            logger.warning(
                "Telegram: chunk %d/%d falló con HTTP %d (%s). Reintentando sin Markdown.",
                i, len(chunks), response.status_code, response.text[:200],
            )
            retry = requests.post(
                url,
                data={"chat_id": chat_id, "text": chunk},
                timeout=30,
            )
            ok = retry.status_code == 200
            if ok:
                logger.info("Telegram: chunk %d/%d enviado (sin Markdown).", i, len(chunks))
            else:
                logger.error("Telegram: chunk %d/%d definitivamente fallido (HTTP %d): %s",
                             i, len(chunks), retry.status_code, retry.text[:200])
            all_ok = all_ok and ok
        except requests.RequestException as exc:
            logger.error("Telegram: excepción de red en chunk %d/%d: %s", i, len(chunks), exc)
            all_ok = False

    return all_ok
