# Football Alerts

A full-stack football match alert application that notifies users about upcoming football matches via email and Google Calendar integration. Users subscribe to leagues, teams, or individual matches and receive alerts at configurable intervals before kickoff.

**Live Demo**: [frontend-alerts.up.railway.app](https://football-alerts.up.railway.app/)

## Quick Start

### Docker Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/erdisonmalko/football-alerts.git
cd football-alerts

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up --build

# Run migrations
docker compose exec api alembic upgrade head

# Access the app
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Local Setup

See [Setup Guide](./docs/SETUP.md) for detailed local development instructions.

## Documentation

- **[Setup Guide](./docs/SETUP.md)** — Complete setup instructions for Docker and local development
- **[Architecture](./docs/ARCHITECTURE.md)** — Project structure, data models, and design patterns
- **[API Reference](./docs/API.md)** — Complete API endpoint documentation
- **[Backend Guide](./docs/BACKEND.md)** — Backend features, stack, and alert schedule
- **[Frontend Guide](./docs/FRONTEND.md)** — Frontend features, components, and styling
- **[Development Guide](./docs/DEVELOPMENT.md)** — Development workflows, testing, and best practices
- **[Deployment Guide](./docs/DEPLOYMENT.md)** — Deployment to Railway and production setup

## Key Features

- **📧 Email Alerts** — 1 week, 3 days, and 6 hours before matches
- **📅 Google Calendar Integration** — Automatically add matches to your calendar
- **⚽ Live Scores** — Real-time match status and score updates
- **🔄 Flexible Subscriptions** — Subscribe to leagues, teams, or specific matches
- **🎯 Personalised Dashboard** — View matches relevant to your subscriptions
- **🏆 Challenges** — Create and join prediction challenges
- **🌍 Multiple Leagues** — Premier League, La Liga, Bundesliga, Ligue 1, Serie A, and more

## Tech Stack

**Backend**: FastAPI, PostgreSQL, SQLAlchemy, Celery, Redis, Google Calendar API, Resend

**Frontend**: React 19, Vite, React Router, Axios

**Infrastructure**: Railway, Supabase, Docker

## Support

- **API Docs** (Interactive): http://localhost:8000/docs
- **Full Documentation**: See files in `/docs` folder
