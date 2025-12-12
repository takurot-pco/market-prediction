"""
Tests for User model - SPEC Section 4 compliance.
"""
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User


@pytest.fixture
async def async_engine():
    """Create an async engine for testing with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create an async session for testing."""
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


class TestUserModel:
    """Test User model structure and behavior."""

    def test_user_has_uuid_id_column(self) -> None:
        """User should have id column that accepts UUID (SPEC Section 4)."""
        import uuid as uuid_module

        test_uuid = uuid_module.uuid4()
        user = User(
            id=test_uuid,
            email="test@example.com",
            name="Test User",
        )
        assert user.id == test_uuid
        assert isinstance(user.id, UUID)

    def test_user_has_balance_field(self) -> None:
        """User should have balance field (SPEC Section 4)."""
        user = User(email="test@example.com", balance=Decimal("500.00"))
        assert hasattr(user, "balance")
        assert user.balance == Decimal("500.00")

    def test_user_has_department_field(self) -> None:
        """User should have department field (SPEC Section 4)."""
        user = User(email="test@example.com", department="Engineering")
        assert hasattr(user, "department")
        assert user.department == "Engineering"

    def test_user_has_updated_at_field(self) -> None:
        """User should have updated_at field (SPEC Section 4)."""
        user = User(email="test@example.com")
        assert hasattr(user, "updated_at")

    def test_user_role_accepts_values(self) -> None:
        """User role should accept role values."""
        user = User(email="test@example.com", role="moderator")
        assert user.role == "moderator"

    def test_user_role_valid_values(self) -> None:
        """User role should accept valid values: admin, moderator, user."""
        for role in ["admin", "moderator", "user"]:
            user = User(email=f"{role}@example.com", role=role)
            assert user.role == role


class TestUserModelDatabase:
    """Test User model database operations."""

    @pytest.mark.asyncio
    async def test_create_user(self, async_session: AsyncSession) -> None:
        """Test creating a user in the database."""
        user = User(
            email="test@example.com",
            name="Test User",
            department="Engineering",
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, UUID)
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.department == "Engineering"
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_defaults_on_create(self, async_session: AsyncSession) -> None:
        """Test that default values are applied on create (SPEC Section 4)."""
        user = User(email="defaults@example.com")
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # UUID should be auto-generated
        assert user.id is not None
        assert isinstance(user.id, UUID)
        # Balance should default to 1000.00
        assert user.balance == Decimal("1000.00")
        # Role should default to 'user'
        assert user.role == "user"

    @pytest.mark.asyncio
    async def test_user_balance_precision(self, async_session: AsyncSession) -> None:
        """Test that balance maintains decimal precision."""
        user = User(
            email="test@example.com",
            balance=Decimal("1234.56"),
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        assert user.balance == Decimal("1234.56")

    @pytest.mark.asyncio
    async def test_user_table_columns(self, async_session: AsyncSession) -> None:
        """Verify all required columns exist in users table (SPEC Section 4)."""
        # Get table columns via raw SQL (SQLite compatible)
        result = await async_session.execute(text("PRAGMA table_info(users)"))
        columns = {row[1] for row in result.fetchall()}

        required_columns = {
            "id",
            "email",
            "name",
            "role",
            "department",
            "balance",
            "created_at",
            "updated_at",
        }
        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    @pytest.mark.asyncio
    async def test_user_email_unique(self, async_session: AsyncSession) -> None:
        """Test that email is unique."""
        user1 = User(email="unique@example.com")
        async_session.add(user1)
        await async_session.commit()

        user2 = User(email="unique@example.com")
        async_session.add(user2)

        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await async_session.commit()
