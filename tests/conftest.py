import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import get_db
from app.models.models import Base
from app.core.config import settings

# Disable SSL for local/CI connections (asyncpg tries SSL by default)
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
    """Create all tables before integration tests, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(setup_db) -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(setup_db) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """Client pre-authenticated with a test user."""
    await client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    })
    await client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "TestPass123!",
    })
    return client