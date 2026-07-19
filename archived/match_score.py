# import pandas as pd
# import re

# def clean_technologies(value):
#     if pd.isna(value):
#         return []
#     limpio = re.sub(r"[\[\]']", "", str(value))
#     return [t.strip() for t in limpio.split(",") if t.strip()]

# def calculate_match_score(row, your_technologies, preferred_role, preferred_districts, minimum_acceptable_salary):
#     score = 0

#     offer_technologies = set(clean_technologies(row.get("technologies", "")))
#     if offer_technologies:
#         overlap = len(offer_technologies & set(your_technologies)) / len(offer_technologies)
#     else:
#         overlap = 0
#     score += overlap * 35

#     if row.get("mentions_visa", False):
#         score += 30

#     if str(row.get("role_category", "")).lower() == preferred_role.lower():
#         score += 20

#     if str(row.get("location", "")).strip() in preferred_districts:
#         score += 10

#     minimum_salary = row.get("min_salary", None)
#     if pd.notna(minimum_salary) and minimum_salary >= minimum_acceptable_salary:
#         score += 5

#     return round(score)