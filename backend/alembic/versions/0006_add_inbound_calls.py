"""add inbound_calls table

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-25

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inbound_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("from_number", sa.String(), nullable=False),
        sa.Column("matched_name", sa.String(), nullable=True),
        sa.Column("matched_organization", sa.String(), nullable=True),
        sa.Column("provider_call_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="ringing"),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_inbound_calls_provider_call_id", "inbound_calls", ["provider_call_id"])


def downgrade():
    op.drop_index("ix_inbound_calls_provider_call_id", table_name="inbound_calls")
    op.drop_table("inbound_calls")
