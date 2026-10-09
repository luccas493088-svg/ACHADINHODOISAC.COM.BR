"""Conector Mercado Livre — dry-run (Fase 8)."""
from datetime import date

from app.importers.base import StoreConnector


class MercadoLivreConnector(StoreConnector):
    store = "Mercado Livre"
    credentials_env = ("MERCADOLIVRE_APP_ID", "MERCADOLIVRE_CLIENT_SECRET")

    def fetch(self) -> list[dict]:
        """Fictícios para testes; live lê `credentials()` no futuro."""
        return [
            {
                "nome": "Fone Bluetooth TWS (exemplo)",
                "preco": 89.9,
                "imagem": "",
                "link_afiliado": "https://www.example.com/ml/fone-bluetooth",
                "data_cadastro": date(2026, 9, 1),
            },
            {
                "nome": "Luminária LED Inteligente (exemplo)",
                "preco": 59.9,
                "imagem": "",
                "link_afiliado": "https://www.example.com/ml/luminaria-led",
                "data_cadastro": date(2026, 9, 10),
            },
        ]
