# Job Tracker — Seoul

A personal data pipeline that tracks job offers relevant to foreign tech professionals in Seoul, South Korea, scores each offer against a custom profile, and sends daily alerts for the best matches.

Built as a portfolio project spanning three layers: **Data Analyst** (dashboard), **Data Scientist** (classification model), and **AI Engineer** (automated daily pipeline with notifications).

## Why this project exists

I'm relocating to Seoul on an H-1 visa and using this tool to track and prioritize job opportunities in data analytics, data science, and AI engineering roles — while building a demonstrable, end-to-end project for my own job applications.

## Project structure

```
arc_b_job_tracker/
├── data/
│   ├── raw/                 # manually collected offers (offers.csv)
│   └── processed/           # cleaned data + daily match alerts
├── scraper/
│   └── basic_scraper.py     # cleans raw offers: visa mentions, tech stack extraction
├── model/
│   ├── match_score.py       # rule-based scoring logic (profile match %)
│   └── train_classifier.py  # ML classifier for visa-sponsorship likelihood
├── dashboard/
│   └── app.py                # Streamlit dashboard (KPIs, charts, filterable table)
├── agent/
│   ├── notifier.py           # Telegram notification module
│   └── daily_pipeline.py     # orchestrates scoring + notification
└── .github/workflows/
    └── daily_job.yml          # scheduled GitHub Action, runs the pipeline daily
```

## The three layers

**1. Data Analyst layer — `dashboard/app.py`**
An interactive Streamlit dashboard showing tracked offers, most requested technologies, weekly trends, visa-mention rates by source, offers by district, and a filterable table.

**2. Data Scientist layer — `model/`**
- `match_score.py`: a weighted scoring function combining tech-stack overlap, visa/sponsorship signals, role category, location, and salary into a single 0–100 match score per offer.
- `train_classifier.py`: a TF-IDF + Random Forest classifier trained to predict visa-sponsorship likelihood from offer descriptions.

**3. AI Engineer layer — `agent/`**
A daily automated pipeline (`daily_pipeline.py`), scheduled via GitHub Actions, that scores all tracked offers, filters the top matches, and sends a summary via Telegram — no manual checking required.

## Data sources and legal approach

Job data is collected **manually** from LinkedIn, Wanted, JobKorea, and other Korean job boards — not scraped. Most Korean job platforms (JobKorea, Saramin, Wanted, KOWORK) explicitly prohibit automated scraping/crawling in their terms of service, and Korean courts have previously ruled against unauthorized scraping of job listing databases (e.g. the Saramin vs. JobKorea case). To stay on the right side of this, all offer data here was collected by hand, respecting each platform's terms of use.

Future versions of this project may integrate the **Work-Net public API** (via data.go.kr, Korea's official open data portal) as a legal, automated data source.

## Setup

```bash
git clone <your-repo-url>
cd arc_b_job_tracker
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root (never commit this file):
```
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Running it

**Dashboard:**
```bash
streamlit run dashboard/app.py
```

**Daily pipeline (manual run):**
```bash
python agent/daily_pipeline.py
```

**Automated schedule:** the pipeline runs daily via GitHub Actions (`.github/workflows/daily_job.yml`). To enable it on your own fork, add `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` as repository secrets under Settings → Secrets and variables → Actions.

## Current status

- [x] Manual data collection (100 offers from LinkedIn, Wanted, JobKorea, DevKorea)
- [x] Data cleaning pipeline (visa mentions, technology extraction)
- [x] Interactive dashboard with KPIs, trends, and filters
- [x] Rule-based match scoring
- [x] Daily automation pipeline with Telegram notifications
- [x] Scheduled via GitHub Actions
- [ ] Classifier trained on a larger, more balanced dataset (visa mentions are currently rare in the data)
- [ ] Work-Net API integration as a legal automated data source
- [ ] Public demo deployment (Hugging Face Spaces)

## Known limitations

- The visa-sponsorship classifier is trained on a heavily imbalanced dataset (very few offers explicitly mention sponsorship), so its predictive value is currently limited — a rule-based signal (`foreigner_friendly`) is used as a more reliable proxy in the meantime.
- Salary data is available for only a small subset of collected offers, since most Korean job postings don't disclose salary ranges publicly.

## Tech stack

Python, pandas, scikit-learn, Streamlit, Telegram Bot API, GitHub Actions.