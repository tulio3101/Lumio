"""location shares

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "location_shares",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("accuracy_m", sa.Float()),
        sa.Column("position_updated_at", sa.DateTime(timezone=True)),
        sa.Column("contacts_total", sa.Integer(), nullable=False),
        sa.Column("contacts_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stopped_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_location_shares_user_id", "location_shares", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_location_shares_user_id", table_name="location_shares")
    op.drop_table("location_shares")
