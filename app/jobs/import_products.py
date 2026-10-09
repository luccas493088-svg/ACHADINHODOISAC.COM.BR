"""Job manual importar_produtos (Fase 8) — dry-run, sem I/O externo."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.importers import CONNECTORS


def run_import(db: Session, stores: list[str] | None = None) -> dict:
    """Roda os conectores e grava no banco (deduplica pelo link)."""
    started = datetime.now(timezone.utc)
    escolhidas = stores or list(CONNECTORS)
    por_loja: dict[str, dict] = {}
    total_fetched = total_saved = total_duplicates = 0

    for nome in escolhidas:
        conector = CONNECTORS.get(nome)
        if conector is None:
            por_loja[nome] = {"error": "loja desconhecida"}
            continue
        relatorio = conector.save(db, conector.fetch())
        por_loja[nome] = relatorio
        total_fetched += relatorio["fetched"]
        total_saved += relatorio["saved"]
        total_duplicates += relatorio["duplicates"]

    return {
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "stores": por_loja,
        "total_fetched": total_fetched,
        "total_saved": total_saved,
        "total_duplicates": total_duplicates,
        "live": False,
    }
