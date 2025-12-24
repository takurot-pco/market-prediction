"""
Async database session utilities.
"""
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """Create an async SQLAlchemy engine."""
    return create_async_engine(database_url or settings.database_url, future=True)


engine: AsyncEngine = create_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide a scoped async session (FastAPI dependency friendly)."""
    async with AsyncSessionLocal() as session:
        yield session


# Alias for compatibility
get_db = get_session
