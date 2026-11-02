# Currency Converter

A simple, elegant currency converter web application with real-time exchange rates.

## Features

- Real-time exchange rates
- 150+ supported currencies
- Clean, intuitive interface
- Swap currencies with one click
- Historical rate charts (planned)
- Offline-capable with cached rates
- Responsive design

## Project Structure

```
currency_converter/
├── index.html      # Complete app (HTML + CSS + JS)
└── README.md
```

## Getting Started

### Installation

No build step required. Open `index.html` in any browser.

```bash
git clone https://github.com/hemateja566/currency_converter.git
cd currency_converter
open index.html
```

## Usage

1. Enter amount in source currency field
2. Select source currency (dropdown)
3. Select target currency (dropdown)
4. View converted amount instantly
5. Click swap button (⇄) to reverse currencies

## API Integration

### Current: ExchangeRate-API (Free tier)

```javascript
const API_URL = 'https://api.exchangerate-api.com/v4/latest/USD';
```

### Alternative APIs
- [Fixer.io](https://fixer.io/)
- [CurrencyLayer](https://currencylayer.com/)
- [Open Exchange Rates](https://openexchangerates.org/)

### API Key Setup

If using a keyed API:
```javascript
const API_KEY = 'YOUR_API_KEY';
const API_URL = `https://api.apilayer.com/fixer/latest?base=USD&apikey=${API_KEY}`;
```

## Supported Currencies

Major currencies: USD, EUR, GBP, JPY, CHF, CAD, AUD, CNY, INR, BRL, MXN, SGD, HKD, KRW, NZD, SEK, NOK, DKK, PLN, CZK, HUF, ILS, PHP, THB, MYR, IDR, ZAR, TRY, RUB, AED, SAR, QAR, KWD, BHD, OMR + 100 more

## Features in Detail

### Real-time Rates
Fetches latest rates on load and caches for 1 hour.

### Offline Support
Cached rates used when offline. Shows last update timestamp.

### Swap Feature
Instantly reverses from/to currencies.

### Precision
Handles decimal precision appropriately per currency (e.g., JPY = 0 decimals, USD = 2 decimals).

## Customization

Edit `index.html` to modify:
- Default currencies
- Color theme (CSS variables)
- Number of decimal places
- API endpoint

## Deployment

Deploy to any static hosting:
```bash
# GitHub Pages
# Netlify: drag & drop folder
# Vercel: vercel deploy
```

## Limitations (Free Tier)

- Rate limits: ~1000 requests/month
- Update frequency: Daily (not real-time)
- No historical data

## License

MIT License