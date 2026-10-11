import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from redis.asyncio import Redis, ConnectionPool


import app.db.redis as redis_module
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


redis_module.redis_pool = ConnectionPool.from_url(
    settings.redis_test_url,
    decode_responses=True,
)

test_engine = create_async_engine(
    settings.test_db,
    poolclass=NullPool,
)
test_session_local = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with test_session_local() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def session():
    async with test_session_local() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def cleanup():
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE users, refresh_tokens, venues, seats, events, event_seats, reservations RESTART IDENTITY CASCADE"))
    async with Redis(connection_pool=redis_module.redis_pool) as client:
        await client.flushdb()
    yield


@pytest_asyncio.fixture
async def redis():
    client = Redis(connection_pool=redis_module.redis_pool)
    yield client
    await client.aclose()

