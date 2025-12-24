"""
Category Pydantic schemas.
SPEC Section 4 & 5 compliant.
"""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base schema for Category."""

    name: str = Field(..., min_length=1, max_length=50, description="Category name")
    description: str | None = Field(None, description="Category description")
    sort_order: int = Field(0, ge=0, description="Display order (lower first)")


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    id: uuid.UUID = Field(..., description="Category UUID")

    model_config = {"from_attributes": True}
