"""add organization column to calls

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-13

"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("calls", sa.Column("organization", sa.String(), nullable=True))


def downgrade():
    op.drop_column("calls", "organization")
