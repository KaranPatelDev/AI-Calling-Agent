"""rename twilio_call_sid to provider_call_id (switch to Plivo)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-13

"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("calls", "twilio_call_sid", new_column_name="provider_call_id")


def downgrade():
    op.alter_column("calls", "provider_call_id", new_column_name="twilio_call_sid")
