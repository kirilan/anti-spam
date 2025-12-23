"""add body_text to email_scans

Revision ID: 1f3d0c2b4b8e
Revises: e85755999482
Create Date: 2025-12-23 09:12:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1f3d0c2b4b8e"
down_revision: str | None = "91bb03064d41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("email_scans", sa.Column("body_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("email_scans", "body_text")
