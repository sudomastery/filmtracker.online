"""
Shared test fixtures for FilmTracker backend tests.

Uses a separate `filmtracker_test` database and Redis DB 1 to
avoid touching production data.

All async fixtures and tests share a single session-scoped event loop
(asyncio_default_fixture_loop_scope = session,
 asyncio_default_test_loop_scope  = session in pytest.ini).
This avoids asyncpg / aioredis "attached to a different loop" errors
that appear when mixing function-scoped and session-scoped loops.

Test isolation is maintained by:
  - clean_tables  — truncates all rows before every test
  - test_redis    — creates a fresh Redis client + flushdb before every test
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import redis.asyncio as aioredis

from app.main import app
from app.core.database import Base, get_db, get_redis

TEST_DB_URL = "postgresql+asyncpg://roy:-=-=@localhost/filmtracker_test"
TEST_REDIS_URL = "redis://localhost:6379/1"  # DB 1 keeps tests isolated from prod

TABLE_TRUNCATE_SQL = text(
    "TRUNCATE TABLE notifications, watchlist, rating_likes, ratings, "
    "user_genre_preferences, follows, movies, users "
    "RESTART IDENTITY CASCADE"
)


# ─── Schema setup — runs once per session in the session event loop ─────────

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Drop and recreate all tables before the test session starts."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


# ─── Wipe all user data before each test ───────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Truncate all rows before each test."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.connect() as conn:
        await conn.execute(TABLE_TRUNCATE_SQL)
        await conn.commit()
    await engine.dispose()


# ─── Redis on DB 1 (flushed before each test) ──────────────────────────────

@pytest_asyncio.fixture
async def test_redis():
    client = aioredis.from_url(
        TEST_REDIS_URL, encoding="utf-8", decode_responses=True
    )
    await client.flushdb()
    yield client
    await client.aclose()


# ─── Per-test AsyncClient with dependency overrides ────────────────────────

@pytest_asyncio.fixture
async def client(test_redis):
    """
    Fresh engine + HTTP client per test.
    All async objects live in the shared session event loop so asyncpg
    and aioredis never see cross-loop Future errors.
    """
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_redis():
        return test_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
