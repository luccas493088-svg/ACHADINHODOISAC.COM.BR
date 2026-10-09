"""Contrato dos conectores de loja (Fase 8).

Dry-run: `fetch()` nunca toca rede — devolve fictícios. `save()` grava no
banco com deduplicação pelo link. Credenciais via ambiente (nunca no código).
"""
import os
from abc import ABC, abstractmethod
from datetime import date

from sqlalchemy.orm import Session
from app.models.store_product import StoreProduct


class StoreConnector(ABC):
    """Um conector por loja."""

    store: str = "base"
    credentials_env: tuple[str, ...] = ()

    def credentials(self) -> dict[str, str]:
        """Lê credenciais do ambiente (vazio = não configurada)."""
        return {
            key: os.getenv(key, "")
            for key in self.credentials_env
            if os.getenv(key, "")
        }

    def is_configured(self) -> bool:
        return bool(self.credentials())

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Busca produtos (dry-run: fictícios, sem I/O)."""

    def save(self, db: Session, items: list[dict]) -> dict:
        """Grava evitando duplicados pelo link. Retorna o relatório."""
        existing = {
            row[0]
            for row in db.query(StoreProduct.link_afiliado)
            .filter(
                StoreProduct.link_afiliado.in_(
                    [i.get("link_afiliado") for i in items if i.get("link_afiliado")]
                )
            )
            .all()
        } if items else set()

        saved = 0
        duplicates = 0
        for item in items:
            link = item.get("link_afiliado")
            if not link or link in existing:
                duplicates += 1
                continue
            db.add(
                StoreProduct(
                    loja=self.store,
                    nome=item.get("nome", ""),
                    preco=item.get("preco", 0),
                    imagem=item.get("imagem") or None,
                    link_afiliado=link,
                    data_cadastro=item.get("data_cadastro") or date.today(),
                    ativo=item.get("ativo", True),
                )
            )
            existing.add(link)
            saved += 1
        db.commit()
        return {
            "store": self.store,
            "fetched": len(items),
            "saved": saved,
            "duplicates": duplicates,
            "live": False,
        }
