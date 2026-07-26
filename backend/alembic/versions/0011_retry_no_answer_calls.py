"""replace inbound-missed-callback retry with outbound no-answer retry

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-26

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("calls", sa.Column("is_retry", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("calls", sa.Column("retry_call_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.drop_column("calls", "direct_connect")
    op.drop_column("inbound_calls", "auto_callback_call_id")


def downgrade():
    op.add_column("inbound_calls", sa.Column("auto_callback_call_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "calls",
        sa.Column("direct_connect", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.drop_column("calls", "retry_call_id")
    op.drop_column("calls", "is_retry")
