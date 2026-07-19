# 🧠 Job Tracker Korea — AI CV-Driven Job Matching Pipeline

Automated job discovery and ranking system that collects job offers, evaluates them using an LLM (Anthropic), and sends daily personalized alerts based on your **real CV**.

---

## 🚀 Overview

This project is a fully automated pipeline that:

1. Fetches job offers from Jooble API
2. Evaluates each offer using an LLM (Anthropic Claude)
3. Scores each job based on your **actual CV**
4. Filters top matches
5. Sends a daily summary via Telegram

👉 The key feature: **match scoring is personalized using your CV**, not generic rules.

---

## 🧩 Architecture

```
Jooble API → Data Collection → LLM Evaluation → Scoring → CSV Storage → Telegram Alerts
```

---

## 📁 Project Structure

```
arc_b_job_tracker/
│
├── scraper/
│   └── jooble_connector.py       # Fetch job offers from Jooble API
│
├── model/
│   └── llm_judge.py              # LLM evaluation (Anthropic)
│
├── agent/
│   ├── daily_pipeline.py         # Main orchestration pipeline
│   └── notifier.py               # Telegram notifications
│
├── data/
│   ├── raw/
│   │   └── offers.csv            # Raw job offers (historical)
│   │
│   ├── processed/
│   │   ├── processed_offers.csv  # Evaluated offers
│   │   └── alerts_YYYY-MM-DD.csv # Daily filtered results
│   │
│   └── profile/
│       └── cv.txt                # 🔥 YOUR CV (core of the system)
│
├── .github/workflows/
│   └── daily_job.yml             # Daily automation (optional)
│
├── requirements.txt
└── README.md
```

---

## 🧠 Core Concept: CV-Driven Scoring

Unlike traditional job scrapers, this system:

* Uses your **real CV (cv.txt)** as input
* Evaluates each job with an LLM
* Produces a personalized `match_score (0–100)`

### Scoring Logic

* 35% → Technology overlap
* 30% → Visa sponsorship likelihood
* 20% → Role alignment (Data roles prioritized)
* 10% → Location match (Korea preferred)
* 5% → Salary fit

---

## 📄 CV Integration (Critical)

The system reads your CV from:

```
data/profile/cv.txt
```

This file is injected into the LLM prompt and directly affects:

* match_score
* role classification
* visa likelihood
* final ranking

👉 Without this file, the system will fail.

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Create `.env` file

```bash
JOOBLE_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

### 3. Add your CV

Create:

```
data/profile/cv.txt
```

Paste your CV in plain text format.

---

## ▶️ Run the pipeline

```bash
python agent/daily_pipeline.py
```

---

## 📊 Output

### Full dataset

```
data/processed/processed_offers.csv
```

Includes:

* job data
* LLM evaluation
* match_score
* reasoning

---

### Daily alerts

```
data/processed/alerts_YYYY-MM-DD.csv
```

Includes:

* only top matches above threshold

---

## 📲 Telegram Notifications

Daily message includes:

* Top job matches
* Match score (%)
* Visa likelihood
* Short reasoning

Example:

```
🟢 Company X — Data Analyst
Link: ...
Match: 78% | Visa: 65%
"Strong SQL match but unclear visa sponsorship"
```

---

## 🔄 Automation (Optional)

Use GitHub Actions:

```
.github/workflows/daily_job.yml
```

Runs the pipeline automatically every day.

---

## ⚠️ Important Notes

* This project is for **personal use only**
* Do not redistribute job data from Jooble
* Respect API rate limits
* Do not expose your `.env` file

---

## 🧪 Testing Without Jooble API

You can simulate data:

```python
df = pd.DataFrame([
    {
        "company": "Test Company",
        "title": "Data Analyst",
        "location": "Seoul",
        "description": "SQL and Tableau required",
        "link": "http://example.com"
    }
])
```

---

## 🚀 Future Improvements

* Deduplication of offers
* Application tracking (applied / rejected)
* Multi-user support
* Dashboard analytics
* Hybrid scoring (LLM + deterministic rules)

---

## 🧠 Tech Stack

* Python
* Pandas
* Anthropic Claude API
* Jooble API
* Telegram Bot API
* GitHub Actions

---

## 🎯 Goal

Automatically identify and prioritize the **best job opportunities for you**, based on your real profile — without manual searching.

---

## 📄 License

MIT
