"""Amazon Associados — builder de link (Fase 6, dry-run)."""
import os
from urllib.parse import urlencode

from app.integrations.base import AffiliateNetwork

AMAZON_BASE = "https://www.amazon.com.br"


class AmazonNetwork(AffiliateNetwork):
    name = "amazon"

    def _partner_tag(self) -> str:
        return os.getenv("AMAZON_PARTNER_TAG", "")

    def is_configured(self) -> bool:
        return bool(self._partner_tag())

    def build_url(self, external_id: str, **params) -> str:
        """Monta `.../dp/{ASIN}/?tag={partner_tag}` (puro, sem I/O)."""
        tag = params.get("tag", self._partner_tag())
        query = urlencode({"tag": tag}) if tag else ""
        url = f"{AMAZON_BASE}/dp/{external_id}/"
        return f"{url}?{query}" if query else url
