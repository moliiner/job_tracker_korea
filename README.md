# 🚀 AI Job Tracker — South Korea

An automated job tracking pipeline that collects, filters, evaluates, and ranks job offers using AI, with a focus on **Data & AI roles in South Korea**.

---

## 📌 Overview

This project is designed to:

* 🔎 Scrape job offers from Jooble API
* 🧠 Evaluate each offer using an LLM (Claude)
* 📊 Score offers based on relevance to your CV
* 💸 Minimize API cost by evaluating only new offers
* 📬 Send daily summaries via Telegram
* 🗂 Persist historical data for tracking and analysis

---

## ⚙️ Architecture

```
project/
│
├── scraper/
│   └── jooble_connector.py      # Fetch + normalize job offers
│
├── model/
│   └── llm_judge.py             # LLM-based evaluation
│
├── agent/
│   └── daily_pipeline.py        # Main orchestration pipeline
│
├── data/
│   ├── raw/                    # Raw collected offers
│   ├── processed/              # Evaluated + scored offers
│   └── profile/                # Candidate CV
│
└── notifier.py                 # Telegram notifications
```

---

## 🔄 Pipeline Flow

1. **Collect Offers**

   * Uses Jooble API with multiple keyword queries
   * Filters for Korean locations
   * Stores results in `data/raw/offers.csv`

2. **Track Fresh Data**

   * Adds `date_tracked` (execution date)
   * Avoids reliance on unreliable external timestamps

3. **Filter Offers**

   * Keeps only relevant roles (data / AI related)
   * Optional keyword-based filtering

4. **Evaluate with LLM**

   * Uses Claude (Anthropic API)
   * Extracts structured insights:

     * Role category
     * Technologies
     * Visa likelihood
     * Match score

5. **Score Offers**

   * Custom scoring system:

     * Tech overlap (35%)
     * Visa likelihood (30%)
     * Role alignment (20%)
     * Location (10%)
     * Salary (5%)

6. **Store Results**

   * Avoids re-processing already evaluated offers
   * Saves to `processed_offers.csv`

7. **Notify**

   * Sends top matches via Telegram
   * Includes fallback top 5 if none meet threshold

---

## 📊 Scoring Logic

```text
Match Score = 
  Tech overlap        (max 35)
+ Visa likelihood     (max 30)
+ Role alignment      (max 20)
+ Location relevance  (max 10)
+ Salary              (max 5)
```

---

## 🧠 LLM Evaluation

Each job offer is analyzed with a structured prompt:

* Extracts relevant technologies
* Detects visa sponsorship signals
* Evaluates role fit
* Produces a JSON output

Fallback handling ensures robustness if parsing fails.

---

## 💡 Cost Optimization

To minimize LLM API usage:

* ✅ Only evaluates **new offers**
* ✅ Uses `link` as unique identifier
* ✅ Filters by `date_tracked`
* ✅ Skips empty or irrelevant data

---

## 📁 Data Fields

### Raw Data (`offers.csv`)

* company
* title
* location
* description
* link
* source
* date_posted
* date_tracked

### Processed Data

* role_category
* technologies_found
* visa_sponsorship_likelihood
* foreigner_friendly_signal
* salary_meets_minimum
* match_score
* reasoning

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

Fallback:

```
No offers reached threshold → showing top 5
```

---

## 🧪 Setup

### 1. Install dependencies

```bash
pip install pandas requests python-dotenv anthropic
```

---

### 2. Environment variables

Create `.env`:

```env
JOOBLE_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

### 3. Add your CV

```
data/profile/cv.txt
```

---

### 4. Run pipeline

```bash
python agent/daily_pipeline.py
```

---

## 🎯 Target Use Case

* Data professionals targeting **South Korea**
* Candidates needing **visa sponsorship**
* Automated job discovery + ranking
* Daily monitoring with minimal effort

---

## 🔮 Future Improvements

* 🌐 Multi-source scraping (LinkedIn, Indeed)
* 🧠 Embedding-based matching (vector similarity)
* 📈 Dashboard (Streamlit / Supabase)
* 🔔 Real-time alerts
* 🧹 Deduplication via semantic similarity

---

## ⚠️ Notes

* Jooble API may return outdated offers → handled via `date_tracked`
* LLM output is probabilistic → scoring is normalized locally
* Some fields may be `"N/D"` if not available

---

## 📄 License

Personal project — adapt as needed.

---

## 👤 Author

Built for optimizing job search with AI-driven filtering and evaluation.
