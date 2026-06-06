# Backend Overview

The backend is a FastAPI-based REST API that manages user subscriptions, football match data, alerts, and calendar integration.

## Key Features

- **Email Alerts** — Notifies users 1 week, 3 days, and 6 hours before football matches
- **Match Data Sync** — Syncs upcoming matches from football-data.org every 12 hours
- **Live Scores** — Updates match statuses and scores every 15 minutes during match days
- **Google Calendar Integration** — Automatically adds matches to user's Google Calendar
- **Flexible Subscriptions** — Users can subscribe to leagues, teams, or individual matches
- **Challenge System** — Create and participate in prediction challenges
- **Server Integration** — Support for Discord servers and community management

## Technology Stack

| Component | Technology |
|-----------|-----------|
| API Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Web Server | Uvicorn |
| Database | PostgreSQL 16 with [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Task Queue | [Celery](https://docs.celeryq.dev/) |
| Message Broker | Redis |
| Data Source | [football-data.org API](https://www.football-data.org/) (free tier) |
| Email Service | [Resend](https://resend.com/) (free tier: 3k/month) |
| Calendar API | [Google Calendar API](https://developers.google.com/calendar) |
| Auth | JWT + bcrypt |
| Validation | Pydantic |

## Alert Schedule

Alerts are sent based on proximity to match kickoff time:

| Alert Type | Timing | Window |
|-----------|--------|--------|
| 1-week | 1 week before | 6h 59m – 7h 1m |
| 3-days | 3 days before | 2d 23h – 3d 1h |
| 6-hours | 6 hours before | 5h 30m – 6h 30m |

The Celery Beat scheduler runs the alert dispatch task every hour. The `AlertLog` table ensures no duplicate emails are sent for the same match to the same user.

## Background Tasks

### Scheduled Tasks (Celery Beat)

| Task | Schedule | Purpose |
|------|----------|---------|
| `sync_matches_task` | 07:00 and 18:00 UTC | Fetches upcoming matches from football-data.org and stores in database |
| `dispatch_alerts_task` | Every hour | Evaluates all user subscriptions and sends emails for matches in alert windows |
| `update_match_statuses_task` | Every 15 minutes | Polls football-data.org for live match statuses and scores |
| `sync_calendar_task` | 07:30 UTC | Syncs upcoming matches to connected Google Calendars |

### Async Tasks

- **Email Sending** — Handled via Resend API
- **Google Calendar API Calls** — Add/remove events, manage reminders

## Configuration

Configuration is managed via environment variables and Pydantic settings (`core/config.py`):

- `APP_ENV` — Environment (development, staging, production)
- `SECRET_KEY` — JWT secret for token signing
- `ADMIN_KEY` — Admin endpoint protection key
- `DATABASE_URL` — Async PostgreSQL connection string
- `REDIS_URL` — Redis connection for Celery broker
- `FOOTBALL_DATA_API_KEY` — API key for football-data.org
- `RESEND_API_KEY` — API key for email service
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — OAuth credentials

## Database Schema Overview

### Core Tables

- **users** — User accounts with email and hashed password
- **subscriptions** — User subscriptions (league, team, or match)
- **matches** — Football matches with team, score, status, kickoff time
- **alert_logs** — Tracks sent alerts to prevent duplicates
- **google_tokens** — Stores OAuth tokens for Google Calendar
- **google_calendar_events** — Maps matches to calendar events
- **servers** — Discord/community servers
- **server_subscriptions** — Server subscriptions to leagues/teams
- **challenges** — Prediction challenges
- **challenge_entries** — User predictions in challenges

### Relationships

- User → Subscriptions (1:many)
- User → GoogleToken (1:1)
- Subscription → Matches (many:many)
- GoogleToken → GoogleCalendarEvent (1:many)
- Server → ServerSubscription (1:many)
- Challenge → ChallengeEntry (1:many)

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed structure.

## Authentication & Security

- **JWT Tokens** — Bearer tokens with configurable expiry
- **Password Hashing** — bcrypt with salt
- **Admin Endpoints** — Protected by `X-Admin-Key` header
- **OAuth 2.0** — Google Calendar integration uses OAuth 2.0 authorization flow
- **CORS** — Configured for frontend domain
- **Secrets Management** — All sensitive keys stored in environment variables

## Supported Leagues (Free Tier)

The backend integrates with football-data.org's free tier which supports:

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

## API Documentation

The FastAPI backend provides interactive documentation:

- **Swagger UI** — http://localhost:8000/docs
- **ReDoc** — http://localhost:8000/redoc

See [API.md](./API.md) for complete endpoint reference.

## Development Workflow

### Running Services Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Terminal 1: FastAPI server
uvicorn app.v1.main:app --reload

# Terminal 2: Celery worker
celery -A app.v1.tasks.celery_app worker --loglevel=info

# Terminal 3: Celery beat scheduler
celery -A app.v1.tasks.celery_app beat --loglevel=info
```

### Running Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/v1/test_unit_alerts.py

# With coverage
pytest --cov=app tests/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of change"

# Apply migrations
alembic upgrade head

# Revert last migration
alembic downgrade -1
```

## Service Layer

Each domain has a dedicated service class in `services/`:

- **user_service.py** — User operations, subscriptions, profile
- **football_service.py** — HTTP client for football-data.org API
- **match_service.py** — Match sync, alert window logic
- **email_service.py** — Email sending via Resend
- **google_calendar_service.py** — Google Calendar operations
- **server_service.py** — Server/community management
- **challenge_service.py** — Challenge operations

Services are dependency-injected into route handlers for testability and maintainability.

## Error Handling

The backend uses custom exceptions defined in `core/exceptions.py`:

- `ValidationError` — Invalid input
- `AuthenticationError` — Not authenticated
- `AuthorizationError` — Not authorized
- `NotFoundError` — Resource not found
- `ConflictError` — Duplicate resource
- `ServiceError` — Service-layer errors

All exceptions are mapped to appropriate HTTP status codes by FastAPI.

## Logging

Logging is configured in `core/logger.py` with:

- Structured logging with JSON format
- Environment-specific log levels
- Request/response logging middleware
- Task execution logging

## Next Steps

See [SETUP.md](./SETUP.md) for detailed setup instructions.
