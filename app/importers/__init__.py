"""Registro dos conectores por loja (Fase 8)."""
from app.importers.aliexpress import AliExpressConnector
from app.importers.base import StoreConnector
from app.importers.mercadolivre import MercadoLivreConnector
from app.importers.monetizze import MonetizzeConnector
from app.importers.tiktok import TikTokShopConnector

CONNECTORS: dict[str, StoreConnector] = {
    "TikTok Shop": TikTokShopConnector(),
    "Monetizze": MonetizzeConnector(),
    "Mercado Livre": MercadoLivreConnector(),
    "AliExpress": AliExpressConnector(),
}

STORES = tuple(CONNECTORS)


def get_connector(store: str) -> StoreConnector:
    """Retorna o conector da loja (erro claro se desconhecida)."""
    try:
        return CONNECTORS[store]
    except KeyError:
        raise ValueError(
            f"Loja desconhecida: {store!r}. Disponíveis: {sorted(CONNECTORS)}"
        ) from None
