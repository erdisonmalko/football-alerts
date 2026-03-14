import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.db.session import get_db
from app.models.models import Base
from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"ssl": False},
    pool_size=5,
    max_overflow=10,
)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


# ── DB: create once, drop after session ───────────────────────────────────────
@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Unauthenticated client ────────────────────────────────────────────────────
@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def client(setup_db) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ── Authenticated client ──────────────────────────────────────────────────────
@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def auth_client(setup_db) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
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