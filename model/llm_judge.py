# 🔴 REEMPLAZA COMPLETAMENTE TU llm_judge.py POR ESTO

import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


PROMPT_TEMPLATE = """You are an expert job-matching assistant.

CANDIDATE CV:
{cv}

IMPORTANT CONTEXT:
- Candidate wants Data / AI roles
- Candidate holds a Computer Science / Computer Engineering / IT Engineering degree
- Candidate speaks English (C1) and Spanish (native)
- Target: South Korea
- May need visa sponsorship

JOB OFFER:
Company: {company}
Title: {title}
Location: {location}
Description: {description}
Remote: {remote}

Respond with ONLY a raw JSON object. Do NOT use markdown code fences (no ```json, no ```). Do NOT add any text before or after the JSON.

{{
  "role_category": "analyst" | "scientist" | "ai_engineer" | "other",
  "technologies_found": [],
  "visa_sponsorship_likelihood": 0,
  "foreigner_friendly_signal": false,
  "salary_meets_minimum": "unknown",
  "education_match": true | false | "unknown",
  "languages_required": [],
  "match_score": 0,
  "reasoning": ""
}}

For "education_match": set true if the offer explicitly requires, prefers, or is compatible with a Computer Science / Computer Engineering / IT Engineering degree (or doesn't specify a field at all, in which case use "unknown"). Set false only if the offer explicitly requires an unrelated, incompatible degree field.

For "languages_required": list every language explicitly mentioned as required or preferred in the offer (e.g. ["English", "Korean", "Spanish"]). Leave empty if none are mentioned.
"""

def extract_json(raw_text):
    """
    Claude sometimes wraps its response in ```json ... ``` fences despite
    instructions not to. Strip those before parsing.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1).replace("json", "", 1)
    return text.strip()

def evaluate_offer(row, cv):

    prompt = PROMPT_TEMPLATE.format(
        cv=cv,
        company=row.get("company", "N/D"),
        title=row.get("title", "N/D"),
        location=row.get("location", "N/D"),
        description=row.get("description", "N/D"),
        remote=row.get("remote", "N/D")
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=350,  # un poco más de margen por los campos nuevos
        messages=[{"role": "user", "content": prompt}]
    )

    raw_text = message.content[0].text.strip()

    try:
        cleaned = extract_json(raw_text)
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"⚠️  WARNING: could not parse LLM response for '{row.get('title', 'N/D')}'. Raw response was:")
        print(raw_text)
        print("-" * 60)
        result = {
            "role_category": "other",
            "technologies_found": [],
            "visa_sponsorship_likelihood": 0,
            "foreigner_friendly_signal": False,
            "salary_meets_minimum": "unknown",
            "education_match": "unknown",
            "languages_required": [],
            "match_score": 0,
            "reasoning": "Parse error"
        }

    return result