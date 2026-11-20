"""user profile

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-20
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(60)))
    op.add_column("users", sa.Column("phone", sa.String(10)))


def downgrade() -> None:
    op.drop_column("users", "phone")
    op.drop_column("users", "display_name")
