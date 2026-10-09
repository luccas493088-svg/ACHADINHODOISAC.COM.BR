"""Conector TikTok Shop — dry-run (Fase 8)."""
from datetime import date

from app.importers.base import StoreConnector


class TikTokShopConnector(StoreConnector):
    store = "TikTok Shop"
    credentials_env = ("TIKTOK_SHOP_API_KEY", "TIKTOK_SHOP_API_SECRET")

    def fetch(self) -> list[dict]:
        """Fictícios para testes; live lê `credentials()` no futuro."""
        return [
            {
                "nome": "Suporte de Celular Articulado (exemplo)",
                "preco": 29.9,
                "imagem": "",
                "link_afiliado": "https://www.example.com/tiktok/suporte-celular",
                "data_cadastro": date(2026, 9, 2),
            },
            {
                "nome": "Mini Umidificador USB (exemplo)",
                "preco": 45.5,
                "imagem": "",
                "link_afiliado": "https://www.example.com/tiktok/mini-umidificador",
                "data_cadastro": date(2026, 9, 20),
            },
        ]
