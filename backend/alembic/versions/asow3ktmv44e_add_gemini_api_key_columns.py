"""add gemini api key columns to users

Revision ID: asow3ktmv44e
Revises: 4c191330a96c
Create Date: 2025-12-21 16:54:21.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "asow3ktmv44e"
down_revision: str | None = "4c191330a96c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add Gemini API key related columns to users table
    op.add_column("users", sa.Column("encrypted_gemini_api_key", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("gemini_key_updated_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("gemini_model", sa.String(), nullable=True))


def downgrade() -> None:
    # Remove Gemini API key related columns from users table
    op.drop_column("users", "gemini_model")
    op.drop_column("users", "gemini_key_updated_at")
    op.drop_column("users", "encrypted_gemini_api_key")
