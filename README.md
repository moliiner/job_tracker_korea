# 🧠 Job Tracker AI — Automated Job Matching Pipeline

This project is an automated pipeline that collects job offers, evaluates them using an LLM (Anthropic), and notifies the user daily with the most relevant opportunities.

---

## 🚀 Features

* 🔎 Fetch job offers from Jooble API
* 🤖 Evaluate offers using an LLM (Anthropic)
* 📊 Score job relevance based on your profile
* 💾 Store results in structured CSV files
* 📲 Send daily summaries via Telegram
* ⏱️ Fully automated with GitHub Actions

---

## 📁 Project Structure

```
arc_b_job_tracker/
│
├── scraper/
│   └── jooble_connector.py       # Fetch job offers
│
├── model/
│   └── llm_judge.py              # LLM evaluation logic
│
├── agent/
│   ├── daily_pipeline.py         # Main orchestration pipeline
│   └── notifier.py               # Telegram notifications
│
├── data/
│   ├── raw/
│   │   └── offers.csv            # Raw accumulated offers
│   └── processed/
│       ├── processed_offers.csv  # All evaluated offers
│       └── alerts_YYYY-MM-DD.csv # Filtered top offers
│
├── .github/workflows/
│   └── daily_job.yml             # Automation (daily run)
│
├── requirements.txt
└── README.md
```

---

## 🔄 Pipeline Overview

1. **Fetch Offers**

   * Queries Jooble API using predefined keywords
   * Stores results in `data/raw/offers.csv`

2. **Evaluate with LLM**

   * Each job is analyzed using Anthropic
   * Generates:

     * Match score (0–100)
     * Role classification
     * Visa likelihood
     * Tech match

3. **Process & Rank**

   * Combine raw + evaluated data
   * Sort by `match_score`
   * Filter top opportunities

4. **Save Results**

   * `processed_offers.csv` → full dataset
   * `alerts_YYYY-MM-DD.csv` → top matches

5. **Notify**

   * Sends daily summary via Telegram

---

## 📊 Scoring Logic

The match score is based on:

* 35% Technology overlap
* 30% Visa sponsorship likelihood
* 20% Role match
* 10% Location match
* 5% Salary fit

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file:

```
JOOBLE_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## ▶️ Run manually

```bash
python agent/daily_pipeline.py
```

---

## 🤖 Automation

The pipeline runs daily using GitHub Actions:

```
.github/workflows/daily_job.yml
```

---

## 📈 Future Improvements

* Better deduplication logic
* Multi-country support
* Advanced filtering (remote, salary parsing)
* Dashboard analytics
* Model fine-tuning

---

## 🧩 Tech Stack

* Python
* Pandas
* Anthropic API (LLM)
* Jooble API
* Telegram Bot API
* GitHub Actions

---

## 📬 Output Example

* `processed_offers.csv`
* `alerts_2026-07-19.csv`

---

## 🧠 Goal

Help you **automatically discover and prioritize the best job opportunities** based on your profile — without manual searching.

---

## 📄 License

MIT
