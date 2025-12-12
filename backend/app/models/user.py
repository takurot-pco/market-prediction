"""
User model definition.
SPEC Section 4 compliant.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """User entity (SPEC Section 4).

    Attributes:
        id: UUID primary key
        email: Unique email address (max 320 chars)
        name: Display name (max 100 chars)
        role: User role (admin/moderator/user)
        department: Department name (max 100 chars)
        balance: Available point balance (default: 1000.00)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="user", server_default="user"
    )
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("1000.00"),
        server_default="1000.00",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
