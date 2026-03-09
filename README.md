# Football Alerts — Backend

Email-based match reminder service. Notifies users **1 week**, **3 days**, and **6 hours** before
football matches they care about.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 + SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Task Queue | Celery + Redis |
| Match Data | [football-data.org](https://www.football-data.org) (free tier) |
| Email | [Resend](https://resend.com) (free tier: 3k/month) |

---

## Project Structure

```
football-alerts/
├── app/
│   ├── api/routes/
│   │   ├── auth.py        # POST /register, POST /login
│   │   ├── users.py       # GET/PATCH /me, subscriptions CRUD
│   │   ├── football.py    # GET leagues, GET teams
│   │   └── admin.py       # Manual sync + alert preview
│   ├── core/
│   │   ├── config.py      # Settings via pydantic-settings
│   │   └── security.py    # JWT + password hashing
│   ├── db/
│   │   └── session.py     # Async SQLAlchemy engine + get_db()
│   ├── models/
│   │   └── models.py      # User, Subscription, Match, AlertLog
│   ├── schemas/
│   │   └── schemas.py     # Pydantic request/response models
│   ├── services/
│   │   ├── user_service.py      # User + subscription DB ops
│   │   ├── football_service.py  # football-data.org HTTP client
│   │   ├── match_service.py     # Sync + alert window logic
│   │   └── email_service.py     # Resend email sending
│   ├── tasks/
│   │   ├── celery_app.py        # Celery config + beat schedule
│   │   └── alert_tasks.py       # sync_matches + dispatch_alerts tasks
│   └── main.py            # FastAPI app + router registration
├── alembic/               # DB migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Get API keys
- **football-data.org** — [register free](https://www.football-data.org/client/register) → get API key
- **Resend** — [register free](https://resend.com) → create API key + verify sender domain

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your keys
```

### 3. Run with Docker Compose
```bash
docker compose up --build
```

This starts: PostgreSQL, Redis, FastAPI (port 8000), Celery worker, Celery beat scheduler.

### 4. Run migrations (first time)
```bash
docker compose exec api alembic upgrade head
```

### 5. Access the API
- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc

---

## Supported Leagues (free tier)

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

---

## Alert Schedule

| Alert | Sends when... |
|-------|--------------|
| `1_week` | Match is 6h 59m – 7h 1m away |
| `3_days` | Match is 2d 23h – 3d 1h away |
| `6_hours` | Match is 5h 30m – 6h 30m away |

The Celery beat scheduler checks every hour. The `AlertLog` table ensures no duplicate emails.

---

## Key API Endpoints

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login

GET    /api/v1/users/me
PATCH  /api/v1/users/me
GET    /api/v1/users/me/subscriptions
POST   /api/v1/users/me/subscriptions
DELETE /api/v1/users/me/subscriptions/{id}

GET    /api/v1/football/leagues
GET    /api/v1/football/leagues/{code}/teams

POST   /api/v1/admin/sync-matches        (X-Admin-Key header)
GET    /api/v1/admin/upcoming-alerts     (X-Admin-Key header)
```

---

## Development without Docker

```bash
# Create virtual env
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start Postgres + Redis locally, then:
uvicorn app.main:app --reload

# In separate terminals:
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```
