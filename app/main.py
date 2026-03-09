from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, football, users
from app.core.config import settings
from app.db.session import engine
from app.models.models import Base  # noqa: F401 — ensures models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: create tables if they don't exist
    # (In production, use Alembic migrations instead)
    async with engine.begin() as conn:
        if not settings.is_production:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # On shutdown
    await engine.dispose()


app = FastAPI(
    title="Football Alerts API",
    description="Get email reminders for upcoming football matches.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — tighten origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
API_PREFIX = "/api/v1"
app.include_router(auth.router,     prefix=API_PREFIX)
app.include_router(users.router,    prefix=API_PREFIX)
app.include_router(football.router, prefix=API_PREFIX)
app.include_router(admin.router,    prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "env": settings.APP_ENV}
