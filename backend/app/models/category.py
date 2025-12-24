"""
Category model definition.
SPEC Section 4 compliant.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Category(Base):
    """Category entity (SPEC Section 4).

    Categories are used to group related markets together.
    Examples: Product, Sales, HR, Industry Trends.

    Attributes:
        id: UUID primary key
        name: Category name (max 50 chars, unique)
        description: Optional description
        sort_order: Display order (lower numbers first)
    """

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
