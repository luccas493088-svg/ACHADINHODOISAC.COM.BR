"""Conector AliExpress — dry-run (Fase 8)."""
from datetime import date

from app.importers.base import StoreConnector


class AliExpressConnector(StoreConnector):
    store = "AliExpress"
    credentials_env = ("ALIEXPRESS_APP_KEY", "ALIEXPRESS_APP_SECRET")

    def fetch(self) -> list[dict]:
        """Fictícios para testes; live lê `credentials()` no futuro."""
        return [
            {
                "nome": "Teclado Mecânico Mini (exemplo)",
                "preco": 149.9,
                "imagem": "",
                "link_afiliado": "https://www.example.com/ali/teclado-mini",
                "data_cadastro": date(2026, 8, 20),
            },
            {
                "nome": "Cabo USB-C 2m (exemplo)",
                "preco": 15.9,
                "imagem": "",
                "link_afiliado": "https://www.example.com/ali/cabo-usbc",
                "data_cadastro": date(2026, 9, 5),
            },
        ]
