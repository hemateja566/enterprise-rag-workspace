# Weather App

A simple weather application that displays current weather conditions and forecasts using a weather API.

## Features

- Current weather conditions (temperature, humidity, wind, etc.)
- 5-day forecast
- City search with autocomplete
- Geolocation support (detect user's location)
- Responsive design
- Weather icons and animations
- Temperature unit toggle (C°/F°)

## Project Structure

```
weather_app/
├── index.html      # Main HTML structure
├── weather.js      # Application logic & API calls
├── style.css       # Styling
└── README.md
```

## Getting Started

### Prerequisites

- Modern web browser
- Weather API key (OpenWeatherMap, WeatherAPI, etc.)

### Installation

```bash
git clone https://github.com/hemateja566/weather_app.git
cd weather_app
```

### Configuration

1. Get a free API key from [OpenWeatherMap](https://openweathermap.org/api) or [WeatherAPI](https://www.weatherapi.com/)
2. Open `weather.js`
3. Replace `YOUR_API_KEY` with your actual API key:
   ```javascript
   const API_KEY = 'YOUR_API_KEY';
   const BASE_URL = 'https://api.openweathermap.org/data/2.5';
   ```

### Usage

Open `index.html` in your browser.

## API Integration

### OpenWeatherMap (Default)

```javascript
// Current weather
fetch(`${BASE_URL}/weather?q=${city}&appid=${API_KEY}&units=metric`)

// 5-day forecast
fetch(`${BASE_URL}/forecast?q=${city}&appid=${API_KEY}&units=metric`)

// Geolocation
fetch(`${BASE_URL}/weather?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`)
```

## Features in Detail

### Current Weather
- Temperature (feels like, min/max)
- Weather condition (clear, clouds, rain, etc.)
- Humidity, pressure, visibility
- Wind speed & direction
- Sunrise/sunset times

### Forecast
- 5-day / 3-hour interval data
- Daily summary cards
- Precipitation probability

### Search
- City name search
- Enter key support
- Recent searches (localStorage)

### Geolocation
- Browser Geolocation API
- Fallback to IP-based location
- Permission handling

## Customization

### Styling (style.css)
- Color scheme (CSS variables)
- Layout, spacing
- Weather icons (emoji or custom SVG)
- Animations

### Units
Toggle between metric/imperial:
```javascript
const units = 'metric'; // or 'imperial'
```

## Browser Support

- Chrome 50+
- Firefox 45+
- Safari 10+
- Edge 14+

## Deployment

Can be deployed to any static hosting:
- GitHub Pages
- Netlify
- Vercel
- Firebase Hosting

## Security Note

**Never commit API keys to version control.** Use environment variables or a backend proxy for production.

## License

MIT License