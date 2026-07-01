# Clinical Note Intelligence System

An AI-powered pipeline that extracts structured data from unstructured clinical notes and evaluates its own output for accuracy — flagging low-confidence fields for human review.

Built with FastAPI, Groq (Llama 3.1), Pydantic, PostgreSQL, and Streamlit.

---

## The Problem

After every patient visit, a doctor writes a free-text clinical note. An admin then manually reads that note and enters structured data — diagnoses, medications, follow-up dates — into hospital systems. This process is slow, error-prone, and happens millions of times a day across the US.

## What This System Does

1. **Accepts** a raw clinical note via API or browser UI
2. **Extracts** structured fields using an LLM (patient age, sex, diagnoses, medications, follow-up, referrals, risk level)
3. **Evaluates** the extraction with a second LLM call — scoring confidence per field and flagging anything below 70% for human review
4. **Saves** every extraction and evaluation to PostgreSQL with a UUID and timestamp
5. **Displays** results in a Streamlit UI with confidence progress bars and flag indicators

---

## Architecture

```
Doctor submits note (Streamlit UI or API)
        ↓
FastAPI backend receives request
        ↓
LLM #1 (Extractor) — pulls structured fields from note
        ↓
Pydantic validates the extraction schema
        ↓
LLM #2 (Evaluator) — scores confidence per field
        ↓
Python calculates overall confidence (not the LLM — LLMs do math inconsistently)
        ↓
PostgreSQL stores everything with UUID + timestamp
        ↓
Streamlit renders extraction + confidence scores + flags
```

---

## Key Engineering Decisions

**Why two LLM calls?**
The extractor returns structured data confidently even when it's wrong. The evaluator reads both the original note and the extraction side by side, catching mismatches a single-pass system would miss.

**Why calculate confidence in Python, not the LLM?**
During development, the LLM returned `0.0` for overall confidence inconsistently despite correct individual field scores. Tracing with a debug line confirmed the LLM was doing the averaging unreliably. Moving the calculation to Python (simple average of field scores) made it deterministic.

**Why Pydantic for output validation?**
LLMs return text. Production systems need typed, validated data. Pydantic enforces schema on every LLM response — if a required field is missing or the wrong type, it fails loudly rather than silently passing bad data downstream.

**Why PostgreSQL over a file or in-memory store?**
Clinical notes need auditability. A doctor needs to ask "show me all notes from today that need review" — that requires queryable, persistent storage with timestamps, not a list that disappears on server restart.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Provider | Groq (llama-3.1-8b-instant) |
| Backend | FastAPI + Uvicorn |
| Data Validation | Pydantic v2 |
| Database | PostgreSQL + SQLAlchemy |
| Frontend | Streamlit |
| Environment | Python 3.11+, virtualenv |

---

## Project Structure

```
clinical-note-intelligence/
├── backend/
│   ├── main.py          # FastAPI routes (/extract, /health, /notes/needs-review)
│   ├── extractor.py     # LLM Call #1 — structured field extraction
│   ├── evaluator.py     # LLM Call #2 — confidence scoring + flagging
│   ├── models.py        # Pydantic schemas
│   └── database.py      # PostgreSQL connection, ORM models, save/query functions
├── frontend/
│   └── app.py           # Streamlit UI
├── data/
│   └── sample_notes.txt # Synthetic clinical notes for testing
├── .env                 # API keys (not committed)
├── requirements.txt
└── README.md
```

---

## Setup & Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/Indrani0721/clinical-note-intelligence.git
cd clinical-note-intelligence
```

**2. Create and activate virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Create a `.env` file in the root:
```
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://clinical_user:clinical_pass@localhost/clinical_notes_db
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

**5. Set up PostgreSQL**
```bash
psql postgres
```
```sql
CREATE DATABASE clinical_notes_db;
CREATE USER clinical_user WITH PASSWORD 'clinical_pass';
GRANT ALL PRIVILEGES ON DATABASE clinical_notes_db TO clinical_user;
\c clinical_notes_db
GRANT ALL ON SCHEMA public TO clinical_user;
ALTER SCHEMA public OWNER TO clinical_user;
\q
```

**6. Run the FastAPI backend**
```bash
uvicorn backend.main:app --reload
```
API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

**7. Run the Streamlit frontend (new terminal)**
```bash
streamlit run frontend/app.py
```
UI available at `http://localhost:8501`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server health check |
| POST | `/extract` | Submit a clinical note for extraction + evaluation |
| GET | `/notes/needs-review` | Retrieve all notes flagged for human review |

**Example request:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{"note": "58M c/o chest pain x 3 days. Hx of HTN, T2DM. Current meds: metformin 500mg. Starting lisinopril 10mg. Follow up in 2 weeks."}'
```

**Example response:**
```json
{
  "status": "success",
  "note_id": "86c1a9be-7210-4b21-97cc-6dbb45a992c2",
  "extraction": {
    "patient_age": "58",
    "patient_sex": "M",
    "chief_complaint": "chest pain x 3 days",
    "diagnoses": null,
    "current_medications": ["metformin 500mg"],
    "new_medications": ["lisinopril 10mg"],
    "followup": "2 weeks",
    "referrals": null,
    "risk_level": "medium"
  },
  "evaluation": {
    "overall_confidence": 0.78,
    "needs_human_review": true
  }
}
```

---

## What I Learned Building This

**Prompt engineering is real engineering.** I ran the evaluator with three different prompts and got three completely different behaviors — the data never changed, only the instructions did. The evaluator was hallucinating about fields that clearly existed until I reformatted how the extraction was presented to it.

**LLMs shouldn't do math.** The evaluator was returning `0.0` for overall confidence inconsistently. A debug line confirmed the LLM was averaging field scores unreliably. Moving that calculation to Python made it deterministic.

**Evaluation is as hard as extraction.** Building a system that checks its own work is harder than building the system itself. The evaluator made different kinds of mistakes than the extractor — and catching those required understanding what the LLM was actually doing, not just what it returned.

---

## What's Next

- [ ] Docker + deployment to Render or Railway
- [ ] PDF upload support (real clinical notes are PDFs)
- [ ] LangChain integration for more complex extraction chains
- [ ] Red-teaming the evaluator with adversarial notes
- [ ] Authentication layer before any real clinical data touches this

---

## Disclaimer

This is a portfolio project built for learning purposes. It is not intended for use with real patient data and has not been validated for clinical use.
