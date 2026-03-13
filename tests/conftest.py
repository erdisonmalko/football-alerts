import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.db.session import get_db
from app.models.models import Base
from app.core.config import settings


# ── Single event loop for entire test session ─────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    """Override pytest-asyncio's default function-scoped event loop with a
    session-scoped one. This prevents asyncpg connection errors when
    session-scoped fixtures (setup_db) share a DB engine with function-scoped
    fixtures (client, auth_client)."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── DB engine (session-scoped, tied to the single loop above) ─────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"ssl": False},
)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── HTTP client fixtures ───────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(setup_db) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(setup_db) -> AsyncClient:
    """Pre-authenticated client. Registers+logs in a fixed test user."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        # Register (ignore 409 if user already exists from a previous test)
        await ac.post("/api/v1/auth/register", json={
            "email": "testuser@example.com",
            "password": "TestPass123",
            "full_name": "Test User",
        })
        await ac.post("/api/v1/auth/login", data={
            "username": "testuser@example.com",
            "password": "TestPass123",
        })
        yield ac