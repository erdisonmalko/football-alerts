# Football Alerts

A full-stack match alert application that notifies users about upcoming football matches via email and Google Calendar. Users subscribe to leagues, teams, or individual matches and receive alerts at configurable intervals before kickoff.

Live: [frontend-alerts.up.railway.app](https://frontend-alerts.up.railway.app)

---

## Features

- **Match alerts** — email notifications at 1 week, 3 days, and 6 hours before kickoff
- **Google Calendar integration** — add matches directly to your Google Calendar with automatic reminders
- **Live scores** — match statuses and scores updated every 15 minutes during match days
- **Flexible subscriptions** — subscribe to entire leagues, specific teams, or individual matches
- **Personalised dashboard** — view live, upcoming, and today's results for your subscriptions
- **Filtering** — filter matches by league on the dashboard and subscriptions page

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — async REST API
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) — async ORM
- [PostgreSQL](https://www.postgresql.org/) — primary database (hosted on Supabase)
- [Celery](https://docs.celeryq.dev/) + [Redis](https://redis.io/) — async task queue and scheduler
- [Alembic](https://alembic.sqlalchemy.org/) — database migrations
- [Resend](https://resend.com/) — transactional email
- [Google Calendar API](https://developers.google.com/calendar) — calendar event management
- [football-data.org](https://www.football-data.org/) — match data source

**Frontend**
- [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- [React Router](https://reactrouter.com/) — client-side routing
- [Axios](https://axios-http.com/) — HTTP client

**Infrastructure**
- [Railway](https://railway.app/) — deployment (API, Celery worker, Celery beat, frontend)
- [Supabase](https://supabase.com/) — managed PostgreSQL
- Docker — containerisation for all services

---

## Local Setup

### Prerequisites

- Docker and Docker Compose
- A [football-data.org](https://www.football-data.org/) API key (free tier)

### 1. Clone the repository

```bash
git clone https://github.com/erdisonmalko/football-alerts.git
cd football-alerts
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
# App
APP_ENV=development
SECRET_KEY=your-secret-key
ADMIN_KEY=your-admin-key

# Database (Docker service name)
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/football_alerts
DATABASE_URL_SYNC=postgresql://postgres:password@db:5432/football_alerts
DATABASE_USER=postgres
DATABASE_PASSWORD=password

# Redis (Docker service name)
REDIS_URL=redis://redis:6379/0

# Football data
FOOTBALL_DATA_API_KEY=your-api-key

# Email (optional for local dev)
RESEND_API_KEY=your-resend-key
EMAIL_FROM=onboarding@resend.dev
EMAIL_FROM_NAME=Football Alerts

# Frontend
FRONTEND_URL=http://localhost:5173

# Google OAuth (optional for local dev)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### 3. Start all services

```bash
docker compose up --build
```

This starts:
- `api` — FastAPI on [localhost:8000](http://localhost:8000)
- `celery-worker` — processes background tasks
- `celery-beat` — schedules periodic tasks
- `db` — PostgreSQL on port 5432
- `redis` — Redis on port 6379
- `frontend` — React dev server on [localhost:5173](http://localhost:5173)

### 4. Run database migrations

```bash
docker compose exec api alembic upgrade head
```

### 5. Sync match data

Trigger an initial match sync via the admin endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/admin/sync-matches \
  -H "x-admin-key: your-admin-key"
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login |
| `POST` | `/api/v1/auth/logout` | Logout |
| `GET` | `/api/v1/auth/me` | Get current user |

### Users & Subscriptions
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/users/me` | Get user profile |
| `PATCH` | `/api/v1/users/me` | Update profile |
| `DELETE` | `/api/v1/users/me` | Delete account |
| `GET` | `/api/v1/users/me/matches` | Get personalised match feed |
| `GET` | `/api/v1/users/me/subscriptions` | List subscriptions |
| `POST` | `/api/v1/users/me/subscriptions` | Add subscription |
| `DELETE` | `/api/v1/users/me/subscriptions/{id}` | Remove subscription |

### Football Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/football/leagues` | List supported leagues |
| `GET` | `/api/v1/football/leagues/{code}/teams` | List teams in a league |
| `GET` | `/api/v1/football/matches/upcoming` | Browse upcoming matches |

### Google Calendar
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/auth/google/connect` | Start OAuth flow |
| `GET` | `/api/v1/auth/google/status` | Check connection status |
| `DELETE` | `/api/v1/auth/google/disconnect` | Disconnect Google Calendar |
| `POST` | `/api/v1/calendar/matches/add-match/{id}` | Add match to calendar |
| `DELETE` | `/api/v1/calendar/matches/remove-match/{id}` | Remove match from calendar |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/admin/sync-matches` | Trigger match sync |
| `POST` | `/api/v1/admin/dispatch-alerts` | Trigger alert dispatch |
| `POST` | `/api/v1/admin/update-match-statuses` | Trigger live score update |
| `POST` | `/api/v1/admin/sync-calendars` | Trigger calendar sync |
| `GET` | `/api/v1/admin/upcoming-alerts` | Preview upcoming alerts |

---

## Background Tasks

Celery beat runs the following scheduled tasks:

| Task | Schedule | Description |
|------|----------|-------------|
| `sync_matches_task` | 07:00 and 18:00 UTC | Fetches upcoming matches from football-data.org |
| `dispatch_alerts_task` | Every hour | Sends email alerts for matches in alert windows |
| `update_match_statuses_task` | Every 15 minutes | Updates live scores and match statuses |
| `sync_calendar_task` | 07:30 UTC | Syncs upcoming matches to connected Google Calendars |

---

## Supported Leagues

Premier League, La Liga, Serie A, Bundesliga, Ligue 1, UEFA Champions League, Primeira Liga, Eredivisie