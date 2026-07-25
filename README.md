# 🚀 AI Job Tracker — South Korea

An automated job tracking pipeline that collects, filters, evaluates, and ranks job offers using AI, with a focus on **Data & AI roles in South Korea**.

---

## 📌 Overview

This project is designed to:

* 🔎 Fetch job offers via official job-search APIs (not scraping — see [Legal approach](#-legal-approach))
* 🧠 Evaluate each offer using an LLM (Claude)
* 📊 Score offers based on relevance to your CV
* 💸 Minimize API cost by evaluating only new offers, once
* 📬 Send daily Telegram summaries, prioritizing what's new **today**
* 🗂 Persist historical data for tracking and analysis

---

## ⚙️ Architecture

```
project/
│
├── scraper/
│   └── jooble_connector.py      # Fetch + normalize job offers (Jooble API — active)
│
├── model/
│   └── llm_judge.py             # LLM-based evaluation
│
├── agent/
│   ├── daily_pipeline.py        # Main orchestration pipeline
│   └── notifier.py              # Telegram notifications
│
├── data/
│   ├── raw/                     # Raw collected offers
│   ├── processed/               # Evaluated + scored offers (full history)
│   └── profile/                 # Candidate CV
│
├── archived/                    # Earlier version of the project — see "Project history"
│   ├── basic_scraper.py
│   ├── match_score.py
│   └── train_classifier.py
│
└── dashboard/
    └── app.py                   # Streamlit dashboard
```

---

## 🌐 Data sources — current and planned

Access to Korean job-platform APIs has turned out to be its own small negotiation per platform, so the project is built to support multiple sources rather than depend on just one:

| Source | Status | Notes |
|---|---|---|
| **Jooble** | ✅ Active | International aggregator with Korea coverage; no business registration required; results are filtered in code to confirm they're Korea-based, since the API has no dedicated country parameter |
| **Saramin** | ⏳ Application submitted, awaiting approval | Access key generated after login, once approved |
| **Wanted** | ⏳ Application submitted, likely blocked | Requires a Korean Business Registration Number; contacted support to ask about individual access |
| **Work-Net** (data.go.kr) | 🔜 Planned, blocked until relocation | Requires identity verification tied to a Korean phone number / ARC — can't be completed from outside Korea |

---

## ⚖️ Legal approach

Job data is sourced **exclusively through official, sanctioned APIs** — never by scraping job board websites directly. Most Korean job platforms (JobKorea, Saramin, Wanted, KOWORK) explicitly prohibit automated scraping/crawling in their terms of service, and Korean courts have previously ruled against unauthorized scraping of job listing databases (e.g. the Saramin vs. JobKorea case). Using each platform's official API — even when that means waiting for manual approval — is the deliberate alternative to scraping, not a shortcut around it.

---

## 🔄 Pipeline Flow

1. **Collect Offers**

   * Queries active APIs (currently Jooble) with multiple keyword queries
   * Filters for Korean locations
   * Stores results in `data/raw/offers.csv`

2. **Track Fresh Data**

   * Adds `date_tracked` (execution date) to every offer
   * Avoids reliance on unreliable/missing external timestamps

3. **Filter Offers**

   * Keeps only relevant roles (data / AI related)
   * Skips offers already evaluated in a previous run (by `link`), so the LLM never re-evaluates — and never re-charges for — the same offer twice

4. **Evaluate with LLM**

   * Uses Claude (Anthropic API) alongside the candidate's CV as context
   * Extracts structured signals:

     * Role category
     * Technologies found
     * Visa sponsorship likelihood
     * Foreigner-friendly signal
     * Education fit (Computer Science / Computer Engineering / IT Engineering)
     * Required languages (English, Spanish, Korean, etc.)

5. **Score Offers**

   * Deterministic scoring computed in Python from the LLM's extracted signals (not left to the LLM to self-score, for reproducibility):

```text
Match Score =
  Tech overlap          (max 25)
+ Visa likelihood        (max 25)
+ Role alignment         (max 15)
+ Location relevance     (max 10)
+ Salary                 (max 5)
+ Education fit          (max 10)
+ Language fit           (max 10)
```

6. **Store Results**

   * Full evaluation history saved to `processed_offers.csv`
   * Never re-processes already-evaluated offers

7. **Notify**

   * Sends **today's** top matches via Telegram — offers from previous days are never resurfaced as if they were new
   * Falls back to today's top 5 if none meet the threshold
   * If no new offers were found at all today, says so explicitly instead of showing nothing or old data

---

## 🧠 LLM Evaluation

Each job offer is analyzed with a structured prompt that instructs the model to respond with raw JSON only (no markdown fences). Robust parsing strips any stray code fences before decoding, and only genuine JSON errors trigger the fallback — other errors (network, auth) are allowed to surface instead of being silently swallowed.

---

## 💡 Cost Optimization

To minimize LLM API usage:

* ✅ Only evaluates **new offers**, identified by `link`
* ✅ Never re-evaluates offers already present in `processed_offers.csv`
* ✅ Skips empty or irrelevant data before calling the LLM
* ✅ Uses Claude Haiku (the cheapest current-generation model) — sufficient for structured extraction, no need for a larger model

---

## 📁 Data Fields

### Raw Data (`offers.csv`)

* company, title, location, description, link, source, date_tracked

### Processed Data

* role_category, technologies_found, visa_sponsorship_likelihood, foreigner_friendly_signal, salary_meets_minimum, education_match, languages_required, match_score, reasoning

---

## 🖥 Example Console Output

```
🔎 Evaluating 1/5
🏢 MinIO
💼 Site Reliability Engineer
🌍 South Korea
🔗 https://...
----------------------------------------
✅ Match: 72%
🛂 Visa: 65%
🧠 Strong data infrastructure + AI relevance
```

---

## 📬 Telegram Alerts

Daily message format:

```
🟢 Company — Role
Link
Match: 75% | Visa: 60%
Reasoning...
```

Fallback (today has offers, none reach the threshold):

```
🟠 No offers reached the threshold today. Showing today's top 5 anyway.
```

Fallback (no new offers found today at all):

```
⚪ No new offers were found today. Best matches from previous days, for reference.
```

---

## 📜 Project history — why there's an `archived/` folder

The first version of this project collected offers manually, extracted signals with regex, and trained a Random Forest classifier (`train_classifier.py`) on that manually-labeled data. That version is kept in `archived/` rather than deleted: it documents a valid earlier approach, retired for a concrete reason — with only ~100 manually-collected offers and just 1 positive example of "mentions visa sponsorship," there wasn't enough labeled data to train a classifier that learned anything beyond predicting the majority class. The project moved to an LLM-based evaluator instead, which doesn't require labeled training data to interpret free-text job descriptions.

---

## 🧪 Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment variables

Create `.env` in the project root (never commit this file):

```env
JOOBLE_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
# Added as each source gets approved:
# SARAMIN_ACCESS_KEY=
# WANTED_API_KEY=
# WORKNET_API_KEY=
```

### 3. Add your CV

```
data/profile/cv.txt
```

### 4. Run the pipeline

```bash
python agent/daily_pipeline.py
```

### 5. Run the dashboard

```bash
streamlit run dashboard/app.py
```

---

## 🎯 Target Use Case

* Data / AI professionals targeting **South Korea**
* Candidates needing **visa sponsorship**
* Automated job discovery + ranking, without re-checking the same listings by hand every day
* Daily monitoring with minimal manual effort

---

## 🔮 Future Improvements

* 🌐 Additional sources: Saramin, Wanted, Work-Net (pending approvals — see [Data sources](#-data-sources--current-and-planned))
* 🧠 Embedding-based matching (vector similarity) as an alternative/complement to LLM scoring
* 📈 Public dashboard deployment (Hugging Face Spaces / Streamlit Community Cloud)
* 🔔 Real-time alerts instead of a daily batch
* 🧹 Deduplication via semantic similarity, for near-duplicate postings across sources

---

## ⚠️ Notes

* Jooble's API has no explicit country filter; Korea-only filtering is enforced afterward in code by checking the offer's location text — a reasonable but not airtight safeguard
* LLM output is probabilistic by nature — the final match score is computed deterministically in Python from the LLM's extracted signals, not left to the LLM to self-score, so identical inputs always produce the same score
* Some fields may show `"N/D"` if not available in the source data

---

## 📄 License

Personal project — adapt as needed.

---

## 👤 Author

Built by Javier Moliner Navarro, as part of relocating to Seoul and optimizing the job search with an AI-driven tracking and evaluation pipeline.
