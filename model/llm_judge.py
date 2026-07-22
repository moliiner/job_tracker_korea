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
- Target: South Korea
- May need visa sponsorship

JOB OFFER:
Company: {company}
Title: {title}
Location: {location}
Description: {description}
Remote: {remote}

Respond ONLY with valid JSON:

{{
  "role_category": "analyst" | "scientist" | "ai_engineer" | "other",
  "technologies_found": [],
  "visa_sponsorship_likelihood": 0,
  "foreigner_friendly_signal": false,
  "salary_meets_minimum": "unknown",
  "match_score": 0,
  "reasoning": ""
}}
"""


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
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_text = message.content[0].text.strip()

    try:
        result = json.loads(raw_text)
    except:
        result = {
            "role_category": "other",
            "technologies_found": [],
            "visa_sponsorship_likelihood": 0,
            "foreigner_friendly_signal": False,
            "salary_meets_minimum": "unknown",
            "match_score": 0,
            "reasoning": "Parse error"
        }

    return result