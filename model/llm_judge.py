import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Your profile: adjust to your real values ---
USER_PROFILE = {
    "technologies": ["Python", "SQL", "Tableau", "AWS", "Docker", "Pandas", "PyTorch", "BI", "TensorFlow"],
    "preferred_roles": ["data analyst", "data scientist", "AI engineer"],
    "preferred_districts": ["Seoul", "Gangnam", "Pangyo", "Seongsu"],
    "minimum_salary_krw": 30000000 #KRW/year
}

PROMPT_TEMPLATE = """You are evaluating a job offer for a candidate relocating to Seoul, South Korea on an H-1 visa, applying for data analyst / data scientist / AI engineer roles.

Candidate profile:
- Technologies: {technologies}
- Preferred roles: {preferred_roles}
- Preferred districts: {preferred_districts}
- Minimum acceptable salary (KRW/year): {minimum_salary}

Job offer to evaluate:
Company: {company}
Title: {title}
Location: {location}
Description: {description}

Evaluate this offer and respond with ONLY a JSON object (no preamble, no markdown fences), with exactly this structure:
{{
  "role_category": "analyst" | "scientist" | "ai_engineer" | "other",
  "technologies_found": ["list", "of", "technologies", "mentioned"],
  "visa_sponsorship_likelihood": 0-100,
  "foreigner_friendly_signal": true | false,
  "salary_meets_minimum": true | false | "unknown",
  "match_score": 0-100,
  "reasoning": "one short sentence explaining the match_score"
}}

Weight the match_score approximately as: 35% technology overlap, 30% visa/sponsorship likelihood, 20% role category match, 10% location match, 5% salary fit.
"""

def evaluate_offer(row):
    prompt = PROMPT_TEMPLATE.format(
        technologies=", ".join(USER_PROFILE["technologies"]),
        preferred_roles=", ".join(USER_PROFILE["preferred_roles"]),
        preferred_districts=", ".join(USER_PROFILE["preferred_districts"]),
        minimum_salary=USER_PROFILE["minimum_salary_krw"],
        company=row.get("company", "N/D"),
        title=row.get("title", "N/D"),
        location=row.get("location", "N/D"),
        description=row.get("description", "")
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",  # cheaper/faster model, sufficient for this repetitive task
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_text = message.content[0].text.strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback in case the model adds stray text despite instructions
        result = {
            "role_category": "other",
            "technologies_found": [],
            "visa_sponsorship_likelihood": 0,
            "foreigner_friendly_signal": False,
            "salary_meets_minimum": "unknown",
            "match_score": 0,
            "reasoning": "Could not parse model response"
        }

    return result