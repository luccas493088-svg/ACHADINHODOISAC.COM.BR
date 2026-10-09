"""Conector Monetizze — dry-run (Fase 8)."""
from datetime import date

from app.importers.base import StoreConnector


class MonetizzeConnector(StoreConnector):
    store = "Monetizze"
    credentials_env = ("MONETIZZE_API_KEY",)

    def fetch(self) -> list[dict]:
        """Fictícios para testes; live lê `credentials()` no futuro."""
        return [
            {
                "nome": "Curso Organização Financeira (exemplo)",
                "preco": 97.0,
                "imagem": "",
                "link_afiliado": "https://www.example.com/monetizze/curso-financas",
                "data_cadastro": date(2026, 8, 15),
            },
            {
                "nome": "E-book Receitas Fit (exemplo)",
                "preco": 19.9,
                "imagem": "",
                "link_afiliado": "https://www.example.com/monetizze/ebook-receitas",
                "data_cadastro": date(2026, 9, 25),
            },
        ]
