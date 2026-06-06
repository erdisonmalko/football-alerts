# Architecture

## Project Structure

```
football-alerts/
├── app/
│   └── v1/
│       ├── main.py                # FastAPI app + router registration
│       ├── api/routes/
│       │   ├── auth.py            # POST /register, POST /login, Google OAuth
│       │   ├── users.py           # GET/PATCH /me, subscriptions CRUD
│       │   ├── football.py        # GET leagues, GET teams
│       │   ├── challenges.py      # Challenge operations
│       │   ├── admin.py           # Manual sync + alert preview
│       │   └── calendar.py        # Google Calendar integration
│       ├── core/
│       │   ├── config.py          # Settings via pydantic-settings
│       │   ├── exceptions.py      # Custom exception classes
│       │   ├── logger.py          # Logging configuration
│       │   └── security.py        # JWT + password hashing
│       ├── db/
│       │   ├── session.py         # Async SQLAlchemy engine + get_db()
│       │   └── celery_session.py  # Async session for Celery tasks
│       ├── models/
│       │   └── models.py          # User, Subscription, Match, AlertLog, GoogleToken, etc.
│       ├── schemas/
│       │   └── schemas.py         # Pydantic request/response models
│       ├── services/
│       │   ├── user_service.py       # User + subscription DB ops
│       │   ├── football_service.py   # football-data.org HTTP client
│       │   ├── match_service.py      # Sync + alert window logic
│       │   ├── email_service.py      # Resend email sending
│       │   ├── google_calendar_service.py # Google Calendar API operations
│       │   ├── server_service.py     # Server management
│       │   ├── challenge_service.py  # Challenge operations
│       │   └── server_mapper.py      # Utility for server subscriptions
│       └── tasks/
│           ├── celery_app.py         # Celery config + beat schedule
│           ├── alert_tasks.py        # sync_matches + dispatch_alerts tasks
│           └── async_task.py         # Other async tasks
├── alembic/                   # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── frontend/v1/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── api/                 # API client utilities
│   │   ├── components/          # React components
│   │   ├── context/             # Context providers (auth, etc.)
│   │   ├── pages/               # Page components
│   │   └── styles/              # CSS modules
│   └── public/
├── tests/
│   ├── v1/
│   │   ├── conftest.py
│   │   ├── test_unit_alerts.py
│   │   ├── integration/
│   │   └── services/
│   └── README.md
├── helpers/
│   └── python/seed/
│       └── seed_db.py
├── docs/
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── requirements.txt
├── requirements-test.txt
├── pyproject.toml
└── README.md
```

## Data Models

### Core Entities

- **User** — Application user with email, password hash
- **Subscription** — User's subscription to a league, team, or match
- **Match** — Football match with teams, score, status, kickoff time
- **AlertLog** — Tracks sent alerts to prevent duplicates
- **GoogleToken** — OAuth tokens for Google Calendar integration
- **GoogleCalendarEvent** — Maps matches to Google Calendar events
- **Server** — Discord/community servers
- **ServerSubscription** — Server's subscriptions to leagues/teams
- **Challenge** — User challenges with results and winners
- **ChallengeEntry** — Individual user entry in a challenge

### Database Relations

- User → Subscriptions (1:many)
- User → GoogleToken (1:1)
- Subscription → Match (many:many via matches table)
- GoogleToken → GoogleCalendarEvent (1:many)
- Server → ServerSubscription (1:many)
- Server → Challenge (1:many)
- Challenge → ChallengeEntry (1:many)

## Backend Stack

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Task Queue | Celery |
| Cache/Broker | Redis |
| Match Data | football-data.org API |
| Email Service | Resend |
| Calendar API | Google Calendar |
| Auth | JWT + bcrypt |

## Frontend Stack

| Component | Technology |
|-----------|-----------|
| Framework | React 19 |
| Build Tool | Vite |
| Routing | React Router |
| HTTP Client | Axios |
| Styling | CSS Modules |

## Deployment Stack

| Service | Platform |
|---------|----------|
| API, Celery, Frontend | Railway |
| Database | Supabase (managed PostgreSQL) |
| Redis | Railway or external provider |
| Containerization | Docker |

## Key Design Patterns

### Service Layer Pattern
Business logic is separated into service classes (`*_service.py`):
- Each service handles a specific domain (users, football data, email, etc.)
- Services are dependency-injected into routes for testability
- Database operations are encapsulated in services

### Task Queue Pattern
Long-running operations are handled asynchronously via Celery:
- **Scheduled tasks** — Celery Beat runs periodic jobs (match sync, alert dispatch)
- **Result tracking** — AlertLog prevents duplicate email sends
- **Error handling** — Failed tasks can be retried with exponential backoff

### Alert Window Logic
Alerts are sent in three windows relative to match kickoff:
- **1 week** — 6h 59m to 7h 1m before
- **3 days** — 2d 23h to 3d 1h before
- **6 hours** — 5h 30m to 6h 30m before

The scheduler checks hourly; AlertLog ensures no duplicates.

### Google Calendar Integration
1. User initiates OAuth flow at `/api/v1/auth/google/connect`
2. After authorization, token stored in GoogleToken table
3. User can add/remove matches to calendar
4. Background job syncs upcoming matches to Google Calendar

## Supported Leagues (Free Tier)

| Code | League | Country |
|------|--------|---------|
| PL   | Premier League | England |
| PD   | La Liga | Spain |
| SA   | Serie A | Italy |
| BL1  | Bundesliga | Germany |
| FL1  | Ligue 1 | France |
| CL   | Champions League | Europe |
| EL   | Europa League | Europe |
| PPL  | Primeira Liga | Portugal |
| DED  | Eredivisie | Netherlands |

## Background Tasks Schedule

| Task | Schedule | Description |
|------|----------|-------------|
| `sync_matches_task` | 07:00 and 18:00 UTC | Fetches upcoming matches from football-data.org |
| `dispatch_alerts_task` | Every hour | Sends email alerts for matches in alert windows |
| `update_match_statuses_task` | Every 15 minutes | Updates live scores and match statuses |
| `sync_calendar_task` | 07:30 UTC | Syncs upcoming matches to Google Calendars |

## Security

- **Authentication** — JWT tokens with configurable expiry
- **Password Security** — bcrypt hashing with salt
- **Admin Endpoints** — Protected by X-Admin-Key header
- **OAuth** — Google OAuth 2.0 for calendar integration
- **CORS** — Configured for frontend URL
- **Environment Variables** — Sensitive keys never committed to repo
