# Space Explorer

A React-based web application for exploring space data including planets, missions, astronauts, and space agencies.

## Live Demo

**[space-explorer-gamma.vercel.app](https://space-explorer-gamma.vercel.app)**

## Features

- Browse planets with detailed information
- View historic and upcoming space missions
- Astronaut profiles and achievements
- Space agency directory
- Responsive design for all devices
- Real-time data from backend API

## Tech Stack

- **Frontend**: React 18 + Vite
- **Styling**: CSS3 / CSS Modules
- **API**: REST (connects to space-backend)
- **Deployment**: Vercel
- **Linting**: ESLint

## Project Structure

```
space-explorer/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── PlanetCard.jsx
│   │   ├── MissionCard.jsx
│   │   ├── AstronautCard.jsx
│   │   └── Navbar.jsx
│   ├── pages/              # Page components
│   │   ├── Home.jsx
│   │   ├── Planets.jsx
│   │   ├── Missions.jsx
│   │   ├── Astronauts.jsx
│   │   └── Agencies.jsx
│   ├── services/           # API services
│   │   └── api.js
│   ├── hooks/              # Custom React hooks
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── index.html
├── package.json
├── vite.config.js
├── eslint.config.js
├── db.json                 # Local fallback data
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd space-explorer
npm install
```

### Development

```bash
# Start dev server (connects to backend on port 3001)
npm run dev
```

Runs at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

Create `.env` file:
```env
VITE_API_BASE_URL=http://localhost:3001
```

## API Integration

The app connects to the [Space Backend](https://github.com/hemateja566/space-backend) for data. Ensure the backend is running on port 3001, or update `VITE_API_BASE_URL`.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Components

### PlanetCard
Displays planet image, name, type, moons count, distance from sun.

### MissionCard
Shows mission name, year, status, description.

### AstronautCard
Astronaut name, nationality, mission count, profile image.

### Navbar
Navigation between Home, Planets, Missions, Astronauts, Agencies.

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project in Vercel
3. Set environment variable `VITE_API_BASE_URL` to production backend URL
4. Deploy

### Other Platforms

Build output in `dist/` folder can be deployed to any static hosting.

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run linting: `npm run lint`
5. Submit Pull Request

## License

MIT License