# Price Tracking Alert System

A full-stack application that monitors product prices and sends alerts when prices drop below a threshold.

## Features

- Track prices from multiple e-commerce sites
- Set custom price thresholds for alerts
- Email/notification alerts when prices drop
- Historical price charts
- User dashboard for managing tracked products
- Automated price checking via cron jobs

## Tech Stack

**Backend:**
- Python (Flask/FastAPI)
- SQLite/PostgreSQL database
- BeautifulSoup/Selenium for scraping
- APScheduler for cron jobs

**Frontend:**
- HTML/CSS/JavaScript
- Chart.js for price visualization

## Project Structure

```
price-tracking-alert-system/
├── backend/
│   ├── app.py              # Main application entry
│   ├── models.py           # Database models
│   ├── scraper.py          # Price scraping logic
│   ├── alerts.py           # Alert notification system
│   ├── scheduler.py        # Automated price checks
│   ├── requirements.txt    # Python dependencies
│   └── config.py           # Configuration
├── frontend/
│   ├── index.html          # Dashboard
│   ├── style.css           # Styling
│   ├── app.js              # Frontend logic
│   └── charts.js           # Price chart visualization
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js (optional, for frontend build tools)
- pip

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp config.example.py config.py  # Edit with your settings
python app.py
```

### Frontend Setup

```bash
cd frontend
# Open index.html directly in browser, or serve with:
python -m http.server 8000
# Or use any static server
```

## Configuration

Create a `config.py` in backend with:
```python
# Database
DATABASE_URL = "sqlite:///prices.db"

# Email alerts
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"

# Scraping
REQUEST_DELAY = 2  # seconds between requests
USER_AGENT = "Mozilla/5.0..."
```

## Usage

1. Start the backend server
2. Open frontend in browser
3. Add products to track with target prices
4. System automatically checks prices on schedule
5. Receive alerts when prices drop

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all tracked products |
| POST | `/api/products` | Add new product to track |
| GET | `/api/products/<id>` | Get product details & history |
| DELETE | `/api/products/<id>` | Remove product |
| POST | `/api/check-price/<id>` | Manual price check |

## Deployment

- **Backend**: Heroku, Railway, Render, or any Python hosting
- **Frontend**: Netlify, Vercel, GitHub Pages
- **Database**: PostgreSQL (recommended for production)
- **Scheduler**: Use platform cron or separate worker

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License