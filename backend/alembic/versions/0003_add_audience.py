"""add audience column to calls

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-13

"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("calls", sa.Column("audience", sa.String(), nullable=False, server_default="buyer"))
    op.create_index("ix_calls_audience", "calls", ["audience"])


def downgrade():
    op.drop_index("ix_calls_audience", table_name="calls")
    op.drop_column("calls", "audience")
