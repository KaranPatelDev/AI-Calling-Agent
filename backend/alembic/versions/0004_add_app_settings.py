"""add app_settings table for buyer/seller default scripts

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-13

"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_script", sa.Text(), nullable=True),
        sa.Column("seller_script", sa.Text(), nullable=True),
    )
    op.execute("INSERT INTO app_settings (id, buyer_script, seller_script) VALUES (1, NULL, NULL)")


def downgrade():
    op.drop_table("app_settings")
