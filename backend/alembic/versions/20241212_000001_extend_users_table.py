"""Extend users table for SPEC compliance.

Revision ID: 20241212_000001
Revises: 20241203_000001
Create Date: 2025-12-12 12:00:00.000000

Changes:
- id: Integer -> UUID
- Add department column (VARCHAR 100)
- Add balance column (NUMERIC 12,2, default 1000.00)
- Add updated_at column (TIMESTAMP with timezone)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241212_000001"
down_revision = "20241203_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get the current connection's dialect
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Add new columns
    op.add_column(
        "users",
        sa.Column("department", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "balance",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="1000.00",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    if dialect == "postgresql":
        # PostgreSQL: Change id column from Integer to UUID
        op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

        # Add temporary UUID column
        op.add_column(
            "users",
            sa.Column("new_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

        # Generate UUIDs for existing rows
        op.execute("UPDATE users SET new_id = uuid_generate_v4()")

        # Make new_id not nullable
        op.alter_column("users", "new_id", nullable=False)

        # Drop old primary key constraint and id column
        op.drop_constraint("users_pkey", "users", type_="primary")
        op.drop_column("users", "id")

        # Rename new_id to id
        op.alter_column("users", "new_id", new_column_name="id")

        # Add primary key constraint on new id column
        op.create_primary_key("users_pkey", "users", ["id"])
    else:
        # SQLite: Keep integer ID (SQLite doesn't support UUID natively)
        # The model uses UUID but SQLAlchemy handles the conversion
        pass


def downgrade() -> None:
    # Get the current connection's dialect
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # PostgreSQL: This is a destructive operation - UUID to Integer conversion
        # Add temporary Integer column
        op.add_column(
            "users",
            sa.Column("old_id", sa.Integer(), autoincrement=True, nullable=True),
        )

        # Create a sequence for the integer IDs
        op.execute("CREATE SEQUENCE IF NOT EXISTS users_id_seq")
        op.execute(
            "SELECT setval('users_id_seq', COALESCE((SELECT MAX(old_id) FROM users), 0) + 1)"
        )
        op.execute("UPDATE users SET old_id = nextval('users_id_seq') WHERE old_id IS NULL")

        op.alter_column("users", "old_id", nullable=False)

        # Drop UUID primary key
        op.drop_constraint("users_pkey", "users", type_="primary")
        op.drop_column("users", "id")

        # Rename old_id to id
        op.alter_column("users", "old_id", new_column_name="id")

        # Add primary key constraint
        op.create_primary_key("users_pkey", "users", ["id"])

    # Drop new columns (common for both dialects)
    op.drop_column("users", "updated_at")
    op.drop_column("users", "balance")
    op.drop_column("users", "department")
