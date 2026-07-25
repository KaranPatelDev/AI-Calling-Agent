"""add per-call speech_rate override

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-25

"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("calls", sa.Column("speech_rate", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("calls", "speech_rate")
