"""Fase 6 — camada de integrações com redes de afiliados.

Contratos + dry-run: nenhum chamado externo acontece sem a flag explícita
`AFFILIATE_LIVE=1` E credenciais configuradas. Leitura de credenciais via
ambiente direto (sem tocar `app/config.py`).
"""
from app.integrations.amazon import AmazonNetwork
from app.integrations.base import (
    AffiliateNetwork,
    DryRunError,
    OfferInfo,
)
from app.integrations.mercadolivre import MercadoLivreNetwork
from app.integrations.monetizze import MonetizzeNetwork
from app.integrations.registry import (
    NETWORKS,
    available_networks,
    build_affiliate_url,
    get_network,
)

__all__ = [
    "AffiliateNetwork",
    "DryRunError",
    "OfferInfo",
    "AmazonNetwork",
    "MercadoLivreNetwork",
    "MonetizzeNetwork",
    "NETWORKS",
    "available_networks",
    "build_affiliate_url",
    "get_network",
]
