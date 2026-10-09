"""Fase 8 - store_products (vitrine com cadastro automático futuro)

Revision ID: fase8_store_products
Revises: fase6_webhook_events
Create Date: 2026-10-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fase8_store_products'
down_revision: Union[str, Sequence[str], None] = 'fase6_webhook_events'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "store_products",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("loja", sa.String(50), nullable=False, index=True),
        sa.Column("nome", sa.String(300), nullable=False),
        sa.Column(
            "preco", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.Column("imagem", sa.String(500), nullable=True),
        sa.Column(
            "link_afiliado",
            sa.String(500),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("data_cadastro", sa.Date(), nullable=False, index=True),
        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("store_products")
