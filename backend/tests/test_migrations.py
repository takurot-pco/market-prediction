"""
Tests for Alembic migrations.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import command

BASE_DIR = Path(__file__).resolve().parents[1]


def run_upgrade(database_url: str) -> None:
    """Run Alembic upgrade to head for the given database URL."""
    alembic_cfg = Config(str(BASE_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


async def get_table_columns(engine: AsyncEngine, table: str) -> set[str]:
    """Fetch column names for a table (SQLite pragma)."""
    async with engine.connect() as conn:
        result = await conn.execute(text(f"PRAGMA table_info('{table}')"))
        return {row[1] for row in result}


@pytest.mark.asyncio
async def test_initial_migration_creates_users_table(tmp_path, monkeypatch) -> None:
    """Alembic initial migration should create users table with expected columns."""
    db_file = tmp_path / "test.db"
    database_url = f"sqlite+aiosqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    await asyncio.to_thread(run_upgrade, database_url)

    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        )
        assert result.scalar() == "users"

    columns = await get_table_columns(engine, "users")
    assert {"id", "email", "name", "role", "created_at"}.issubset(columns)
