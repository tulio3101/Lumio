"""user preferences

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-25
"""

import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("voice_language", sa.String(16), nullable=False),
        sa.Column("voice_identifier", sa.String(255)),
        sa.Column("speech_rate", sa.Float(), nullable=False),
        sa.Column("haptics_enabled", sa.Boolean(), nullable=False),
        sa.Column("haptic_intensity", sa.String(16), nullable=False),
        sa.Column("haptic_disabled_events", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
