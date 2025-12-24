"""Create categories table.

Revision ID: 20241224_000001
Revises: 20241212_000001
Create Date: 2024-12-24
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241224_000001"
down_revision: str | None = "20241212_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create categories table."""
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )

    # Create index for sort_order for efficient ordering
    op.create_index("ix_categories_sort_order", "categories", ["sort_order"])


def downgrade() -> None:
    """Drop categories table."""
    op.drop_index("ix_categories_sort_order", table_name="categories")
    op.drop_table("categories")
