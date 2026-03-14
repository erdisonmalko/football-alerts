import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.db.session import get_db
from app.models.models import Base
from app.core.config import settings


# ── Create/drop tables synchronously — no async, no event loop conflicts ──────
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Use the SYNC engine just for table setup/teardown. Simple and reliable."""
    sync_engine = create_engine(settings.DATABASE_URL_SYNC)
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


# ── Async engine for the app to use during tests ──────────────────────────────
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"ssl": False},
)
TestSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


# ── HTTP clients ──────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client() -> AsyncClient:
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