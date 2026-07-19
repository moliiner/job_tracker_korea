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
- Candidate wants to transition into Data Analyst / Data Scientist / AI Engineer roles
- Candidate is targeting South Korea (Seoul, Pangyo, Gangnam)
- Candidate may need visa sponsorship
- Prioritize international-friendly companies

JOB OFFER:
Company: {company}
Title: {title}
Location: {location}
Description: {description}

Evaluate this offer and respond with ONLY a JSON object:

{{
  "role_category": "analyst" | "scientist" | "ai_engineer" | "other",
  "technologies_found": [],
  "visa_sponsorship_likelihood": 0-100,
  "foreigner_friendly_signal": true | false,
  "salary_meets_minimum": true | false | "unknown",
  "match_score": 0-100,
  "reasoning": "short explanation"
}}

SCORING RULES:
- 35% tech overlap with CV
- 30% visa likelihood
- 20% role alignment (DATA roles prioritized)
- 10% location (Korea preferred)
- 5% salary

STRICT RULES:
- Penalize non-data roles heavily
- Penalize jobs requiring native Korean
- Reward SQL, analytics, BI, ML roles
"""


def evaluate_offer(row, cv):

    prompt = PROMPT_TEMPLATE.format(
        cv=cv,
        company=row.get("company", "N/D"),
        title=row.get("title", "N/D"),
        location=row.get("location", "N/D"),
        description=row.get("description", "")
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_text = message.content[0].text.strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
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