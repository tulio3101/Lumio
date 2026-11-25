"""trusted contacts

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-24
"""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trusted_contacts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "email", name="uq_trusted_contacts_user_email"),
    )
    op.create_index("ix_trusted_contacts_user_id", "trusted_contacts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_trusted_contacts_user_id", table_name="trusted_contacts")
    op.drop_table("trusted_contacts")
