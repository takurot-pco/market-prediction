"""
Seed initial categories.
Run with: python -m app.scripts.seed_categories
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.category import Category

# Initial categories as defined in PLAN.md
INITIAL_CATEGORIES = [
    {
        "name": "Product",
        "description": "Product launch dates, feature releases, and development milestones",
        "sort_order": 1,
    },
    {
        "name": "Sales",
        "description": "Sales targets, revenue predictions, and customer acquisition",
        "sort_order": 2,
    },
    {
        "name": "HR",
        "description": "Hiring, team growth, and organizational changes",
        "sort_order": 3,
    },
    {
        "name": "Industry",
        "description": "Industry trends, competitor movements, and market dynamics",
        "sort_order": 4,
    },
]


async def seed_categories(db: AsyncSession) -> list[Category]:
    """Seed initial categories if they don't exist.

    Args:
        db: Database session

    Returns:
        List of created or existing categories
    """
    categories: list[Category] = []

    for cat_data in INITIAL_CATEGORIES:
        # Check if category already exists
        result = await db.execute(
            select(Category).where(Category.name == cat_data["name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Category '{cat_data['name']}' already exists, skipping")
            categories.append(existing)
        else:
            category = Category(**cat_data)
            db.add(category)
            categories.append(category)
            print(f"Creating category '{cat_data['name']}'")

    await db.commit()

    # Refresh all categories
    for cat in categories:
        await db.refresh(cat)

    return categories


async def main() -> None:
    """Main entry point for seeding categories."""
    print("Seeding categories...")

    async with AsyncSessionLocal() as db:
        categories = await seed_categories(db)
        print(f"\nSeeded {len(categories)} categories:")
        for cat in categories:
            print(f"  - {cat.name} (id: {cat.id})")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
