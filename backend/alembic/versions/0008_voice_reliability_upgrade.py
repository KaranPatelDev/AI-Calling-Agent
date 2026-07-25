"""Hindi voice, speed control, cut-off/voicemail detection, auto-callback

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-25

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("calls", sa.Column("answered_by_machine", sa.Boolean(), nullable=False, server_default="false"))

    op.add_column("inbound_calls", sa.Column("missed", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("inbound_calls", sa.Column("auto_callback_call_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.add_column("app_settings", sa.Column("speech_rate", sa.Integer(), nullable=False, server_default="80"))
    op.add_column(
        "app_settings", sa.Column("auto_callback_enabled", sa.Boolean(), nullable=False, server_default="true")
    )
    op.add_column("app_settings", sa.Column("missed_callback_script", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("app_settings", "missed_callback_script")
    op.drop_column("app_settings", "auto_callback_enabled")
    op.drop_column("app_settings", "speech_rate")

    op.drop_column("inbound_calls", "auto_callback_call_id")
    op.drop_column("inbound_calls", "missed")

    op.drop_column("calls", "answered_by_machine")
