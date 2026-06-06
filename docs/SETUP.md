# Setup Guide

This guide covers both Docker-based and local development setups.

## Prerequisites

- Docker and Docker Compose (for Docker setup)
- Python 3.11+ (for local setup)
- A [football-data.org](https://www.football-data.org/) API key (free tier)
- Node.js 18+ and npm (for frontend)

## Environment Variables

Create a `.env` file in the project root:

```env
# App
APP_ENV=development
SECRET_KEY=your-secret-key
ADMIN_KEY=your-admin-key

# Database (Docker service name, or localhost for local dev)
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/football_alerts
DATABASE_URL_SYNC=postgresql://postgres:password@db:5432/football_alerts
DATABASE_USER=postgres
DATABASE_PASSWORD=password

# Redis (Docker service name, or localhost for local dev)
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

## Setup with Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/erdisonmalko/football-alerts.git
cd football-alerts
```

### 2. Configure environment variables

Create and edit `.env` file (see above).

### 3. Start all services

```bash
docker compose up --build
```

This starts:
- **api** — FastAPI on [localhost:8000](http://localhost:8000)
- **celery-worker** — processes background tasks
- **celery-beat** — schedules periodic tasks
- **db** — PostgreSQL on port 5432
- **redis** — Redis on port 6379
- **frontend** — React dev server on [localhost:5173](http://localhost:5173)

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

### 6. Access the application

- **Frontend**: http://localhost:5173
- **API Swagger UI**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc

---

## Local Development Setup

### Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Start PostgreSQL and Redis

Install and run PostgreSQL 16 and Redis locally, then update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/football_alerts
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/football_alerts
REDIS_URL=redis://localhost:6379/0
```

### Run backend services

```bash
# Terminal 1: FastAPI development server
uvicorn app.v1.main:app --reload

# Terminal 2: Celery worker
celery -A app.v1.tasks.celery_app worker --loglevel=info

# Terminal 3: Celery beat scheduler
celery -A app.v1.tasks.celery_app beat --loglevel=info
```

### Run database migrations

```bash
alembic upgrade head
```

---

### Frontend Setup

```bash
cd frontend/v1

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5173

---

## Verify Installation

### Check Backend Health

```bash
curl http://localhost:8000/docs
```

### Check Database Connection

```bash
# Inside Docker
docker compose exec db psql -U postgres -d football_alerts -c "SELECT 1"

# Local
psql -U postgres -d football_alerts -c "SELECT 1"
```

### Run Tests

```bash
# Backend tests
pytest tests/

# With coverage
pytest --cov=app tests/
```

---

## Troubleshooting

### Port already in use

If port 8000, 5173, or 5432 is already in use, modify `docker-compose.yml` or adjust local service ports.

### Database migration errors

```bash
# Reset migrations (development only!)
docker compose exec api alembic downgrade base
docker compose exec api alembic upgrade head
```

### Redis connection issues

Check Redis is running and accessible:

```bash
redis-cli ping  # Should return PONG
```

### Missing environment variables

Ensure all required variables in `.env` are set before starting services.
