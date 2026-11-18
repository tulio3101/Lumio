"""route reroutes

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-17
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "routes", sa.Column("reroute_count", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column("routes", sa.Column("last_rerouted_at", sa.DateTime(timezone=True)))
    op.create_check_constraint("ck_routes_reroute_count", "routes", "reroute_count >= 0")


def downgrade() -> None:
    op.drop_constraint("ck_routes_reroute_count", "routes", type_="check")
    op.drop_column("routes", "last_rerouted_at")
    op.drop_column("routes", "reroute_count")
