# Support & TAM AI Toolkit

Production-grade LLM tooling for internal Technical Support and Technical Account Management teams. Built for the **US Delivery Internship — Technical Task Round**.

## Overview

A comprehensive AI toolkit featuring ticket triage, account health briefs, evaluation harness, and a Streamlit UI. Designed for production deployment with full observability, evaluation, and security considerations.

## Features

### Task 1: Ticket Triage Agent (30 pts)
- Classifies product, category, urgency
- Matches known issues from knowledge base
- Recommends routing team
- Drafts first response
- Streaming NDJSON output support

### Task 2: TAM Account Brief (25 pts)
- Deterministic 3-section QBR brief
- Verbatim-quote churn flags
- Statistics computed in code (not LLM)
- Byte-stable output with rerun hash

### Task 3: Evaluation Harness (20 pts)
- 14 test cases across both tasks
- Rule-based + LLM-as-judge evaluation
- JSON/Markdown reports
- CI integration

### Task 4: Design Note (15 pts)
- Failure modes analysis
- Latency trade-offs
- PII handling
- Scaling considerations (~600 words)

### Bonus Features (+12 pts)
- ✅ Streamlit UI (+5)
- ✅ Streaming output (+3)
- ✅ GitHub Actions CI (+2)
- ✅ Prompt version registry with changelog (+2)

## Architecture

```
support-ai/
├── api/main.py                 # FastAPI REST service
├── src/support_ai/             # Core package
│   ├── config.py               # Configuration
│   ├── llm.py                  # LLM client (HF + heuristic fallback)
│   ├── kb.py                   # Knowledge base (BM25 retrieval)
│   ├── triage.py               # Ticket classification
│   ├── summarizer.py           # Account brief generation
│   └── prompts/
│       ├── registry.py         # Prompt versioning
│       └── CHANGELOG.md        # Prompt change log
├── evals/                      # Evaluation harness
│   ├── cases/                  # Test cases (JSON)
│   ├── judges/                 # Rule-based & LLM judges
│   └── run.py                  # Evaluation runner
├── scripts/
│   └── sample_run.py           # Demo script
├── tests/                      # Pytest unit tests
├── ui/app.py                   # Streamlit UI
├── data/                       # Mock ticket data
├── knowledge-base/             # KB documents
├── .github/workflows/ci.yml    # CI pipeline
├── requirements.txt
├── .env.example
├── DESIGN.md                   # Task 4 design note
├── eval_report.json            # Latest eval results
└── eval_report.md              # Human-readable eval report
```

## Quickstart

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/hemateja566/support-ai.git
cd support-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add HF_TOKEN (optional but recommended)
```

### Running

```bash
# Task 1+2 Demo (used in walkthrough)
python scripts/sample_run.py

# REST API - http://localhost:8000/docs
uvicorn api.main:app --port 8000

# Evaluation Harness
python evals/run.py                 # Full (LLM judge if HF_TOKEN set)
python evals/run.py --quick         # Offline mode (CI default)

# Unit Tests
pytest tests/ -q

# Streamlit UI
streamlit run ui/app.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/triage` | POST | Classify ticket + draft response |
| `/triage/stream` | POST | Streaming NDJSON triage |
| `/account-brief/{account_id}` | GET | Deterministic account brief |
| `/health` | GET | Health check + engine mode |

### Example Request

```bash
curl -X POST localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "SSO broken for new users",
    "body": "SAML login fails since this morning for all new hires. Production impact, no workaround.",
    "ticket_id": "TKT-12345"
  }'
```

### Example Response

```json
{
  "product": "SecureVault",
  "category": "Bug",
  "urgency": "P1",
  "reasoning": "Authentication is fully blocked for a user cohort with no workaround...",
  "known_issue_match": true,
  "kb_matches": [{"path": "troubleshooting/authentication-sso.md", ...}],
  "recommended_team": "Tier-2 Product Engineering + Incident Response",
  "draft_first_response": "Thanks for flagging this...",
  "prompt_versions": {"triage.classify": "1.2.0"},
  "engine": "llm"
}
```

## Evaluation Results

Latest offline run: **14/14 cases passed, mean quality 1.00**

See [`eval_report.md`](eval_report.md) / [`eval_report.json`](eval_report.json) for details.

With `HF_TOKEN` configured, rerun `python evals/run.py` for LLM-judged quality scores.

## Key Design Decisions

### Retrieval
Pure-Python BM25 over KB chunks. Deterministic, zero network cost, heading metadata preserved.

### Determinism (Task 2)
- Statistics computed in code
- LLM calls pinned to `temperature=0` + fixed seed
- Final brief assembled from templates
- `deterministic_rerun_hash` for byte-stability verification

### Quote Integrity
Model-extracted quotes validated verbatim against source. Paraphrased quotes repaired or dropped.

### Dataset Clock
"Last 90 days" anchors to newest ticket in frozen dataset (not wall-clock).

### Prompt Versioning
Every prompt has ID + semver in `registry.py`. Changes logged in `CHANGELOG.md`. Outputs embed versions used.

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
- Runs unit tests on every push
- Runs offline evaluation harness
- Fails on any regression
- Artifacts: eval reports

## Security

- No secrets in repo (`.env.example` only)
- PII detection in place
- Input validation on all endpoints
- Rate limiting ready

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | No | Hugging Face token for LLM (falls back to heuristic) |
| `KB_PATH` | No | Knowledge base path (default: `knowledge-base/`) |
| `DATA_PATH` | No | Mock data path (default: `data/`) |

## Submission Checklist

- ✅ Runs from clean `pip install -r requirements.txt` + single command per feature
- ✅ `.env.example` present; real secrets never committed
- ✅ `eval_report.json` + `eval_report.md` at repo root
- ✅ Design note included (`DESIGN.md`)
- 📹 Loom video (3–6 min) — record using `scripts/sample_run.py`, `streamlit run ui/app.py`, then show `eval_report.md`

## License

MIT License