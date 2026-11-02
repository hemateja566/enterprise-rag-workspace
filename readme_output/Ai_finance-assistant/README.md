# AI Finance Assistant

Full-stack personal finance management application with AI-powered insights, automated categorization, anomaly detection, and SMS alerts.

## Live Architecture

```
┌─────────────┐     REST API      ┌─────────────┐
│  React UI   │ ◄───────────────► │  Flask API  │
│ (Port 3000) │                   │ (Port 5000) │
└─────────────┘                   └──────┬──────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
             │  MySQL DB   │       │   LLM API   │       │   Twilio    │
             │  (Data)     │       │ (Categorize)│       │   (SMS)     │
             └─────────────┘       └─────────────┘       └─────────────┘
                    ▲
                    │
             ┌──────┴──────┐
             │  Cron Job   │
             │ (Ingest +   │
             │  Alerts)    │
             └─────────────┘
```

## Features

- **Transaction Management**: Add, view, categorize transactions
- **AI Categorization**: LLM-powered automatic category assignment
- **Natural Language Q&A**: Ask questions about your spending
- **Trend Analysis**: AI-generated spending summaries
- **Anomaly Detection**: Z-score based outlier detection
- **SMS Alerts**: Twilio notifications for unusual spending
- **Automated Ingestion**: Cron job for bank data sync
- **Dashboard**: Visual spending trends and analytics

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, Chart.js |
| Backend | Python 3.10+, Flask, SQLAlchemy |
| Database | MySQL 8.0+ |
| AI/ML | LLM API (OpenAI/Anthropic/HF), pandas |
| Notifications | Twilio SMS |
| Scheduling | Cron (Linux) / APScheduler |
| Deployment | Docker, Vercel (FE), Railway/Render (BE) |

## Project Structure

```
Ai_finance-assistant/
├── backend/
│   ├── app.py                    # Flask app factory
│   ├── models.py                 # SQLAlchemy models
│   ├── config.py                 # Configuration
│   ├── schema.sql                # Database schema
│   ├── requirements.txt          # Python deps
│   ├── .env.example              # Env template
│   ├── services/
│   │   ├── llm_service.py        # LLM categorization + Q&A
│   │   ├── nlp_service.py        # Trend stats, batch categorize
│   │   └── alert_service.py      # Twilio SMS sending
│   └── cron/
│       └── ingest_and_alert.py   # Scheduled ingestion + alerts
└── frontend/
    ├── package.json
    ├── src/
    │   ├── App.jsx
    │   ├── api.js                # API client
    │   └── components/
    │       ├── Dashboard.jsx     # Spend trends + anomaly scan
    │       └── ChatQA.jsx        # NL Q&A over transactions
    └── vite.config.js
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- LLM API key (OpenAI, Anthropic, or Hugging Face)
- Twilio account (for SMS alerts)

### Backend Setup

```bash
cd backend

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit .env with your credentials:
# DATABASE_URL, LLM_API_KEY, TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM

# Database
mysql -u root -p < schema.sql
# Or let SQLAlchemy create tables on first run

# Run server
python app.py
```

API runs at `http://localhost:5000/api`

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Runs at `http://localhost:3000`, proxies API calls to Flask backend.

### Cron Job (Automated Ingestion + Alerts)

```bash
# Edit crontab
crontab -e

# Every 15 minutes:
*/15 * * * * /path/to/venv/bin/python /path/to/backend/cron/ingest_and_alert.py >> /var/log/finance_ingest.log 2>&1
```

**Important**: Implement `fetch_new_raw_transactions()` in `ingest_and_alert.py` to connect to your actual data source (bank API, CSV drop, Plaid, etc.).

## Configuration (.env)

```env
# Database
DATABASE_URL=mysql+pymysql://user:pass@localhost/finance_db

# LLM (choose one)
LLM_PROVIDER=openai  # or anthropic, huggingface
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+15551234567

# App
SECRET_KEY=your-secret-key
FLASK_ENV=development
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | List user transactions |
| POST | `/api/transactions` | Add + auto-categorize transaction |
| GET | `/api/trends` | Category totals + LLM trend summary |
| POST | `/api/ask` | NL Q&A over user transactions |
| POST | `/api/anomalies/scan` | Run anomaly scan + send alerts |
| GET | `/api/alerts` | List sent alerts |

### Example: Ask Question

```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How much did I spend on dining last month?"}'
```

Response:
```json
{
  "answer": "You spent $342.50 on dining in January 2024...",
  "data": {"category": "Dining", "total": 342.50, "period": "2024-01"},
  "citations": [{"transaction_id": 123, "amount": 45.00, ...}]
}
```

## Database Schema

```sql
-- Users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),  -- For Twilio alerts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    merchant VARCHAR(255),
    transaction_date DATE NOT NULL,
    is_anomaly BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Alerts
CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    transaction_id INT,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);
```

## Anomaly Detection

- **Method**: Z-score on rolling 30-day window per category
- **Threshold**: |z| > 2.5 (configurable)
- **Alert**: SMS via Twilio with transaction details
- **Frequency**: Every cron run (default 15 min)

## Deployment

### Backend (Railway/Render/Heroku)
```bash
# Build command
pip install -r requirements.txt

# Start command
gunicorn app:app
```

### Frontend (Vercel/Netlify)
```bash
npm run build
# Deploy dist/ folder
```

### Database
- Use managed MySQL (PlanetScale, Railway, AWS RDS)
- Run `schema.sql` on first deploy

### Cron
- Use platform scheduler (Render Cron, Railway Cron, GitHub Actions)
- Or deploy `ingest_and_alert.py` as separate worker

## Security

- ✅ Parameterized queries (SQLAlchemy ORM)
- ✅ Environment variables for secrets
- ✅ CORS configured for frontend origin
- ✅ Input validation on all endpoints
- 🔄 Add: Rate limiting, JWT auth, HTTPS enforcement

## License

MIT License