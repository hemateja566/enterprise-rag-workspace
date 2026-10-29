# Doctor Appointment App

A React-based web application for booking and managing doctor appointments.

## Live Demo

**[doctor-app-gules.vercel.app](https://doctor-app-gules.vercel.app)**

## Features

- Browse doctors by specialization
- View doctor profiles, availability, ratings
- Book appointments with date/time selection
- Appointment management (view, cancel, reschedule)
- User authentication (planned)
- Responsive design
- Real-time availability updates

## Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: CSS3 / CSS Modules
- **State Management**: React Hooks
- **Routing**: React Router (planned)
- **Deployment**: Vercel
- **Linting**: ESLint

## Project Structure

```
doctor__ap/
├── public/                 # Static assets
├── src/
│   ├── components/
│   │   ├── DoctorCard.jsx      # Doctor listing card
│   │   ├── DoctorProfile.jsx   # Detailed doctor view
│   │   ├── AppointmentForm.jsx # Booking form
│   │   ├── AppointmentList.jsx # User's appointments
│   │   ├── Navbar.jsx          # Navigation
│   │   └── Footer.jsx
│   ├── pages/
│   │   ├── Home.jsx            # Landing page
│   │   ├── Doctors.jsx         # Doctor listing
│   │   ├── BookAppointment.jsx # Booking flow
│   │   ├── MyAppointments.jsx  # User appointments
│   │   └── Contact.jsx
│   ├── services/
│   │   └── api.js              # API calls (mock/localStorage)
│   ├── hooks/
│   │   └── useAppointments.js  # Appointment logic
│   ├── App.jsx                 # Root component
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles
├── index.html
├── package.json
├── vite.config.js
├── eslint.config.js
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm

### Installation

```bash
cd doctor__ap
npm install
```

### Development

```bash
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

## Current Data Source

Currently uses mock data in `src/services/api.js` and `localStorage` for appointments. Backend integration planned.

## Doctor Data Structure

```javascript
{
  id: 1,
  name: "Dr. Sarah Johnson",
  specialization: "Cardiology",
  experience: "15 years",
  rating: 4.8,
  reviewCount: 124,
  image: "/images/doctor1.jpg",
  availability: [
    { day: "Monday", slots: ["09:00", "10:00", "11:00"] },
    { day: "Wednesday", slots: ["14:00", "15:00", "16:00"] }
  ],
  fee: 150,
  location: "City Medical Center"
}
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Deployment

### Vercel (Current)

Auto-deploys from main branch on GitHub push.

## Planned Features

- [ ] User authentication (signup/login)
- [ ] Backend API integration
- [ ] Email/SMS notifications
- [ ] Payment integration
- [ ] Doctor dashboard
- [ ] Video consultation support
- [ ] Prescription management
- [ ] Medical records
- [ ] Multi-language support

## License

MIT License