"""sos events

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-24
"""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sos_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("accuracy_m", sa.Float()),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("contacts_total", sa.Integer(), nullable=False),
        sa.Column("contacts_sent", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'partial', 'failed')", name="ck_sos_status"
        ),
        sa.CheckConstraint(
            "contacts_sent >= 0 AND contacts_sent <= contacts_total", name="ck_sos_counts"
        ),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_sos_events_user_key"),
    )
    op.create_index("ix_sos_events_user_id", "sos_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_sos_events_user_id", table_name="sos_events")
    op.drop_table("sos_events")
