"""Registro das redes suportadas (Fase 6)."""
from app.integrations.amazon import AmazonNetwork
from app.integrations.base import AffiliateNetwork
from app.integrations.mercadolivre import MercadoLivreNetwork
from app.integrations.monetizze import MonetizzeNetwork

NETWORKS: dict[str, AffiliateNetwork] = {
    "amazon": AmazonNetwork(),
    "mercadolivre": MercadoLivreNetwork(),
    "monetizze": MonetizzeNetwork(),
}


def get_network(name: str) -> AffiliateNetwork:
    """Retorna a rede pelo nome (erro claro se desconhecida)."""
    try:
        return NETWORKS[name]
    except KeyError:
        raise ValueError(
            f"Rede desconhecida: {name!r}. Disponíveis: {sorted(NETWORKS)}"
        ) from None


def available_networks() -> list[str]:
    """Nomes das redes com credenciais configuradas."""
    return [name for name, net in NETWORKS.items() if net.is_configured()]


def build_affiliate_url(network: str, external_id: str, **params) -> str:
    """Atalho: monta link de afiliado pela rede (puro, sem I/O)."""
    return get_network(network).build_url(external_id, **params)
