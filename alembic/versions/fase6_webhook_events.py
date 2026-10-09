"""Fase 6 - conversion_events (webhooks de conversão)

Revision ID: fase6_webhook_events
Revises: fase5_campaigns_metrics
Create Date: 2026-10-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fase6_webhook_events'
down_revision: Union[str, Sequence[str], None] = 'fase5_campaigns_metrics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "conversion_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("network", sa.String(50), nullable=False, index=True),
        sa.Column("external_id", sa.String(200), nullable=False, index=True),
        sa.Column("product_id", sa.Integer(), nullable=True, index=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True, index=True),
        sa.Column(
            "amount", sa.Numeric(precision=10, scale=2), nullable=True
        ),
        sa.Column(
            "currency", sa.String(10), nullable=False, server_default="BRL"
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="received",
        ),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "network", "external_id", name="uq_network_external"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("conversion_events")
