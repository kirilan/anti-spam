"""force_oauth_reauth_for_scope_fix

Revision ID: c8ada720b72d
Revises: c3f7d9a2a1e4
Create Date: 2025-12-24 15:21:36.841044

This migration clears all user OAuth tokens to force re-authentication.
This is necessary because:
1. OAUTHLIB_RELAX_TOKEN_SCOPE was previously set to "1", allowing tokens without required scopes
2. Some users may have tokens without gmail.readonly scope
3. We've now added scope validation to prevent this in the future

After this migration, users will need to log in again and grant all required permissions.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8ada720b72d"
down_revision: str | None = "c3f7d9a2a1e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Clear all OAuth tokens to force re-authentication with proper scopes
    # Users will need to log in again after this migration
    op.execute("""
        UPDATE users
        SET google_access_token = NULL,
            google_refresh_token = NULL
        WHERE google_access_token IS NOT NULL
    """)


def downgrade() -> None:
    # Cannot restore tokens - users will need to re-authenticate
    pass
