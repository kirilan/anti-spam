"""add deleted_at to deletion_requests for soft delete support

Revision ID: 91bb03064d41
Revises: e85755999482
Create Date: 2025-12-22 12:13:28.966505

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "91bb03064d41"
down_revision: str | None = "e85755999482"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add deleted_at timestamp column for soft delete support
    op.add_column("deletion_requests", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index(
        op.f("ix_deletion_requests_deleted_at"), "deletion_requests", ["deleted_at"], unique=False
    )


def downgrade() -> None:
    # Remove deleted_at column and index
    op.drop_index(op.f("ix_deletion_requests_deleted_at"), table_name="deletion_requests")
    op.drop_column("deletion_requests", "deleted_at")
