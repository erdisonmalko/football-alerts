import os
from dotenv import load_dotenv

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.v1.api.routes import (
    admin,
    auth,
    football,
    users,
    google,
    google_calendar,
    servers,
    challenges,
)
from app.v1.core.config import settings
from app.v1.db.session import engine
from app.v1.models.models import Base  # noqa: F401 — ensures models are registered


from app.v1.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

load_dotenv()  # Load environment variables from .env file


async def _wait_for_db(retries: int = 10, delay: float = 3.0) -> None:
    """
    Retry the DB connection until Postgres is actually ready.
    Docker healthcheck confirms the port is open, but the DB process
    can still be initialising internally for a second or two after that.
    """
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database ready — tables created/verified.")
            return
        except (OperationalError, OSError) as exc:
            if attempt == retries:
                raise RuntimeError(
                    f"Could not connect to database after {retries} attempts"
                ) from exc
            logger.warning(
                f"DB not ready yet (attempt {attempt}/{retries}), retrying in {delay}s…"
            )
            await asyncio.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: wait for DB then create tables (dev only; use Alembic in prod)
    if not settings.is_production:
        await _wait_for_db()
    yield
    # On shutdown
    await engine.dispose()


app = FastAPI(
    title="Football Alerts API",
    description="Get email reminders for upcoming football matches.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow_origins must be explicit (never "*") when allow_credentials=True,
# otherwise the browser refuses to send cookies on cross-origin requests.
ALLOWED_ORIGINS = (
    [os.getenv("FRONTEND_URL")]
    if settings.is_production
    else ["http://localhost:5173", "http://127.0.0.1:5173"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(football.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(google.router, prefix=API_PREFIX)
app.include_router(google_calendar.router, prefix=API_PREFIX)
app.include_router(servers.router, prefix=API_PREFIX)
app.include_router(challenges.router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "env": settings.APP_ENV}
