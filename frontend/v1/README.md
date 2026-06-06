# Frontend

React 19 + Vite frontend for Football Alerts application.

## Quick Start

```bash
cd frontend/v1
npm install
npm run dev
```

Development server runs on http://localhost:5173

## Documentation

Detailed documentation is available in the root `/docs` folder:

- **[Frontend Guide](../../docs/FRONTEND.md)** — Features, architecture, and components
- **[Development Guide](../../docs/DEVELOPMENT.md)** — Development workflows and best practices
- **[Setup Guide](../../docs/SETUP.md)** — Complete setup instructions
- **[Deployment Guide](../../docs/DEPLOYMENT.md)** — Deployment to production

## Key Features

- Match alerts via email
- Google Calendar integration
- Live match scores
- Flexible subscriptions (leagues, teams, matches)
- Personalised dashboard
- Prediction challenges
- Responsive design

## Building

```bash
npm run build
```

Outputs optimized bundle to `dist/` directory.

## Environment Variables

Create `.env.local` or use Railway variables:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_FRONTEND_URL=http://localhost:5173
```

## Tech Stack

- React 19
- Vite
- React Router
- Axios
- CSS Modules
