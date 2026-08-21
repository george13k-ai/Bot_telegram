from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "123456:TEST-TOKEN-not-real")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REQUIRED_CHANNEL_ID", "-1001234567890")
os.environ.setdefault("REQUIRED_CHANNEL_URL", "https://t.me/test_channel")
os.environ.setdefault("ADMIN_IDS", "111111,222222")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database.models import Base


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with session_factory() as s:
        yield s

    await engine.dispose()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
