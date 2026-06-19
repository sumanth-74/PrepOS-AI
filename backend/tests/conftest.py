from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from prepos.api.main import create_app
from prepos.core.config import Settings, get_settings
from prepos.core.database import create_engine, dispose_engine
from prepos.infrastructure.db.base import Base


@pytest.fixture
def settings() -> Settings:
    os.environ["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://prepos:prepos@localhost:5432/prepos_test",
    )
    os.environ["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "test-secret-key-for-prepos-backend-foundation-32chars-min",
    )
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
    get_settings.cache_clear()
    return get_settings()


@pytest_asyncio.fixture
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    from sqlalchemy import text

    test_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with test_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        await test_engine.dispose()
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    create_engine(settings)
    yield test_engine
    await dispose_engine()
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
