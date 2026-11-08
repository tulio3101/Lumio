"""active route summary and constraints

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-07
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

OPEN_ROUTE = sa.text("status IN ('active', 'paused')")


def upgrade() -> None:
    op.add_column(
        "routes", sa.Column("distance_meters", sa.Float(), server_default="0", nullable=False)
    )
    op.add_column(
        "routes",
        sa.Column("expected_travel_time_seconds", sa.Float(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        "ck_routes_status", "routes", "status IN ('active', 'paused', 'completed', 'cancelled')"
    )
    op.create_check_constraint("ck_routes_current_step", "routes", "current_step >= 0")
    op.create_index(
        "uq_routes_one_open_per_user",
        "routes",
        ["user_id"],
        unique=True,
        postgresql_where=OPEN_ROUTE,
        sqlite_where=OPEN_ROUTE,
    )


def downgrade() -> None:
    op.drop_index("uq_routes_one_open_per_user", table_name="routes")
    op.drop_constraint("ck_routes_current_step", "routes", type_="check")
    op.drop_constraint("ck_routes_status", "routes", type_="check")
    op.drop_column("routes", "expected_travel_time_seconds")
    op.drop_column("routes", "distance_meters")
