"""add direct_connect flag, drop unused missed_callback_script

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-25

"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "calls",
        sa.Column("direct_connect", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.drop_column("app_settings", "missed_callback_script")


def downgrade():
    op.add_column("app_settings", sa.Column("missed_callback_script", sa.Text(), nullable=True))
    op.drop_column("calls", "direct_connect")
