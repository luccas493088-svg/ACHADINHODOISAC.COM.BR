"""Monetizze — builder de link (Fase 6, dry-run).

O afiliado recebe o link de checkout pronto; aqui só anexamos `src` de
rastreio interno quando informado (puro, sem I/O).
"""
import os
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from app.integrations.base import AffiliateNetwork


class MonetizzeNetwork(AffiliateNetwork):
    name = "monetizze"

    def is_configured(self) -> bool:
        return bool(os.getenv("MONETIZZE_API_KEY", ""))

    def build_url(self, external_id: str, **params) -> str:
        """Anexa `src` de rastreio ao link base (puro, sem I/O)."""
        src = params.get("src")
        if not src:
            return external_id
        parts = urlparse(external_id)
        query = dict(parse_qsl(parts.query))
        query["src"] = src
        return urlunparse(parts._replace(query=urlencode(query)))
