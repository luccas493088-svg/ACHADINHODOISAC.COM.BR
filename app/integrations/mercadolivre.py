"""Mercado Livre — builder de link (Fase 6, dry-run).

Atribuição de afiliado do ML acontece via API oficial (modo live futuro);
aqui o builder só normaliza/passa adiante a URL do anúncio, sem inventar
parâmetros de tracking.
"""
import os

from app.integrations.base import AffiliateNetwork


class MercadoLivreNetwork(AffiliateNetwork):
    name = "mercadolivre"

    def is_configured(self) -> bool:
        return bool(os.getenv("MERCADOLIVRE_APP_ID", ""))

    def build_url(self, external_id: str, **params) -> str:
        """Retorna a URL do anúncio (puro, sem I/O).

        `external_id` pode ser o ID do anúncio (`MLB...`) ou a URL completa.
        """
        if external_id.startswith(("http://", "https://")):
            return external_id
        return f"https://www.mercadolivre.com.br/itm/{external_id}"
