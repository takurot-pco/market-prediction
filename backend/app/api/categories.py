"""
Category API endpoints.
SPEC Section 5 compliant.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.rbac import RoleChecker, UserRole
from app.db.session import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List all categories",
    description="Get all categories ordered by sort_order. Available to all authenticated users.",
)
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _user: dict[str, Any] = Depends(RoleChecker(UserRole.USER)),
) -> list[Category]:
    """List all categories ordered by sort_order.

    Returns:
        List of categories ordered by sort_order ascending.
    """
    result = await db.execute(select(Category).order_by(Category.sort_order))
    return list(result.scalars().all())


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Create a new category. Admin only.",
)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict[str, Any] = Depends(RoleChecker(UserRole.ADMIN)),
) -> Category:
    """Create a new category.

    Args:
        category_data: Category creation data

    Returns:
        The created category

    Raises:
        ValidationError: If category name already exists
    """
    category = Category(
        name=category_data.name,
        description=category_data.description,
        sort_order=category_data.sort_order,
    )

    db.add(category)

    try:
        await db.commit()
        await db.refresh(category)
    except IntegrityError as e:
        await db.rollback()
        raise ValidationError(
            message=f"Category with name '{category_data.name}' already exists",
            details={"field": "name", "value": category_data.name},
        ) from e

    return category
