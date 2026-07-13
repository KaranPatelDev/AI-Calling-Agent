"""create calls table

Revision ID: 0001
Revises:
Create Date: 2026-07-13

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipient_name", sa.String(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=False),
        sa.Column("script_text", sa.Text(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("twilio_call_sid", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_calls_status", "calls", ["status"])
    op.create_index("ix_calls_scheduled_at", "calls", ["scheduled_at"])


def downgrade():
    op.drop_index("ix_calls_scheduled_at", table_name="calls")
    op.drop_index("ix_calls_status", table_name="calls")
    op.drop_table("calls")
