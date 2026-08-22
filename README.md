<p align="center">
  <img src="./assets/job_tracker_korea.png"
       width="180"
       height="180"
       style="border-radius: 50%; object-fit: cover; border: 2px solid #ddd;" />
</p>

<h1 align="center">
   <strong>🇰🇷 AI Job Tracker — South Korea</strong>
</h1>


<p align="center">
  An automated job tracking pipeline that collects, filters, evaluates, and ranks job offers using AI, with a focus on Data & AI roles in South Korea.
</p>


## 📌 Overview

This project is designed to:

* 🔎 Fetch job offers via official job-search APIs *(no scraping — see Legal approach)*
* 🧠 Evaluate each offer using an LLM (Claude)
* 📊 Score offers based on relevance to your CV
* 💸 Minimize API cost by evaluating only new offers
* 📬 Send daily Telegram summaries prioritizing **today's opportunities**
* 🗂 Persist historical data for tracking and analysis

---

## ⚙️ Architecture

```
project/

├── scraper/
│   └── jooble_connector.py      # Fetch + normalize job offers

├── model/
│   └── llm_judge.py             # LLM-based evaluation

├── agent/
│   ├── daily_pipeline.py        # Main orchestration pipeline
│   └── notifier.py              # Telegram notifications

├── data/
│   ├── raw/                    # Raw collected offers
│   ├── processed/              # Evaluated + scored offers
│   └── profile/                # Candidate CV

├── archived/                   # Previous ML-based version
│   ├── basic_scraper.py
│   ├── match_score.py
│   └── train_classifier.py

└── dashboard/
    └── app.py                  # Streamlit dashboard
```

---

## 🌐 Data Sources — Current & Planned

| Source       | Status     | Notes                                 |
| ------------ | ---------- | ------------------------------------- |
| **Jooble**   | ✅ Active   | Aggregator with Korea coverage        |
| **Saramin**  | ⏳ Pending  | Requires approval                     |
| **Work-Net** | 🔜 Planned | Requires Korean identity verification |

---

## ⚖️ Legal Approach

All job data is sourced **exclusively via official APIs**.

No scraping is used.

This ensures:

* Compliance with platform Terms of Service
* Alignment with Korean legal precedents
* Long-term sustainability of the project

---

## 🔄 Pipeline Flow

### 1. Collect Offers

* Queries APIs (Jooble & Careerjet currently)
* Filters Korea-based roles
* Stores data in `data/raw/offers.csv`

### 2. Track Fresh Data

* Adds `date_tracked`
* Avoids unreliable external timestamps

### 3. Filter Offers

* Keeps Data / AI roles only
* Skips already processed offers

### 4. LLM Evaluation

Extracts structured signals:

* Role category
* Technologies
* Visa sponsorship likelihood
* Foreigner-friendly signal
* Education fit
* Languages required

### 5. Scoring (Deterministic)

```
Match Score =
  Tech overlap           (max 25)
+ Visa likelihood        (max 25)
+ Role alignment         (max 15)
+ Location relevance     (max 10)
+ Salary                 (max 5)
+ Education fit          (max 10)
+ Language fit           (max 10)
```

### 6. Store Results

* Saved in `processed_offers.csv`
* Never re-evaluated twice

### 7. Notify

* Daily Telegram alerts with **new offers only**
* Smart fallback messaging if needed

---

## 🧠 LLM Evaluation

* Uses **Claude (Anthropic API)**
* Strict JSON output parsing
* Robust error handling
* Deterministic scoring outside the LLM

---

## 💡 Cost Optimization

* ✅ Evaluates only **new offers**
* ✅ No duplicate LLM calls
* ✅ Filters irrelevant data early
* ✅ Uses **Claude Haiku 4.5** (cost-efficient)

---

## 📁 Data Fields

### Raw (`offers.csv`)

* company, title, location, description, link, source, date_tracked

### Processed

* role_category
* technologies_found
* visa_sponsorship_likelihood
* foreigner_friendly_signal
* salary_meets_minimum
* education_match
* languages_required
* match_score
* reasoning

---

## 🖥 Example Output

```
🔎 Evaluating 1/5
🏢 MinIO
💼 Site Reliability Engineer
🌍 South Korea

✅ Match: 72%
🛂 Visa: 65%
🧠 Strong data infrastructure + AI relevance
```

---

## 📬 Telegram Alerts

**Daily format:**

```
🟢 Company — Role
Link
Match: 75% | Visa: 60%
Reasoning...
```

Fallback cases:

* 🟠 No offers met threshold → show top 5
* ⚪ No new offers → notify explicitly

---

## 📜 Project History

Earlier version (in `archived/`) used:

* Manual data collection
* Regex extraction
* Random Forest classifier

It was replaced due to **insufficient labeled data**, making ML ineffective.

LLMs removed the need for labeled datasets.

---

## 🧪 Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment variables

```env
JOOBLE_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Add your CV

```
data/profile/cv.txt
```

### 4. Run pipeline

```bash
python agent/daily_pipeline.py
```

### 5. Run dashboard

```bash
streamlit run dashboard/app.py
```

---

## 🎯 Target Use Case

* Data / AI professionals targeting **South Korea**
* Candidates needing **visa sponsorship**
* Automated job tracking with **zero manual repetition**

---

## 🔮 Future Improvements

* Additional APIs (Work-Net)
* Embedding-based matching
* Public dashboard deployment
* Real-time alerts
* Semantic deduplication

---

## ⚠️ Notes

* Jooble lacks strict country filtering → handled in code
* LLM outputs are probabilistic → scoring is deterministic
* Some fields may show `"N/D"` if unavailable

---

## 📄 License

Personal project — adapt as needed.

---

## 👤 Author

Built by **Javier Moliner Navarro**, as part of relocating to Seoul 🇰🇷 and optimizing the job search with an AI-driven tracking and evaluation pipeline.

---

## ⭐ Support

If you find this useful, consider giving the project a star ⭐


