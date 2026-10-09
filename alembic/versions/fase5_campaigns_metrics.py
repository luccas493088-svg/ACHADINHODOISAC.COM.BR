"""Fase 5 - campaigns, click_events, product.campaign_id

Revision ID: fase5_campaigns_metrics
Revises: users_init
Create Date: 2026-10-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fase5_campaigns_metrics'
down_revision: Union[str, Sequence[str], None] = 'users_init'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False, index=True),
        sa.Column("slug", sa.String(200), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "click_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("product_id", sa.Integer(), nullable=False, index=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True, index=True),
        sa.Column("ip_hash", sa.String(64), nullable=True, index=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("referrer", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], ondelete="SET NULL"
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "campaign_id",
            sa.Integer(),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_products_campaign_id", "products", ["campaign_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_products_campaign_id", table_name="products")
    op.drop_column("products", "campaign_id")
    op.drop_table("click_events")
    op.drop_table("campaigns")
