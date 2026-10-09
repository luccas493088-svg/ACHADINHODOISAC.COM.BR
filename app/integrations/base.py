"""Contratos da camada de integrações (Fase 6).

Toda rede implementa `AffiliateNetwork`. Chamadas de rede reais passam por
`_require_live()`, que só libera com `AFFILIATE_LIVE=1` + `is_configured()`.
"""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class DryRunError(RuntimeError):
    """Levantado quando código tenta chamada externa com live desativado."""


@dataclass(frozen=True)
class OfferInfo:
    network: str
    external_id: str
    title: str
    price: Optional[float]
    url: str
    in_stock: Optional[bool] = None


def live_enabled() -> bool:
    """Flag explícita que libera chamadas externas. Padrão: desligado."""
    return os.getenv("AFFILIATE_LIVE", "0") == "1"


class AffiliateNetwork(ABC):
    """Contrato que toda rede de afiliados deve implementar."""

    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """True quando as credenciais necessárias estão no ambiente."""

    @abstractmethod
    def build_url(self, external_id: str, **params) -> str:
        """Monta o link de afiliado (puro, sem I/O)."""

    def _require_live(self) -> None:
        if not live_enabled():
            raise DryRunError(
                f"[{self.name}] modo dry-run: defina AFFILIATE_LIVE=1 "
                "para chamadas externas"
            )
        if not self.is_configured():
            raise DryRunError(
                f"[{self.name}] credenciais ausentes no ambiente"
            )

    def fetch_offer(self, external_id: str) -> OfferInfo:
        """Busca a oferta na rede (live). Base: só o guard, sem I/O."""
        self._require_live()
        raise NotImplementedError(
            f"[{self.name}] fetch_offer live ainda não implementado"
        )
