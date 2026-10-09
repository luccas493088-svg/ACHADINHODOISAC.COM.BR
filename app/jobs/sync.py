"""Job manual de sincronia — auditoria offline dos links de afiliado.

Dry-run de verdade: nenhum socket, nenhum HTTP. O job valida formato,
classifica por rede via host da URL e relata o que precisa de atenção.
O enriquecimento live (preço/estoque via `fetch_offer`) entra depois,
atrás da flag `AFFILIATE_LIVE=1`.
"""
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from app.models.product import Product

HOST_NETWORK = (
    ("amazon.", "amazon"),
    ("mercadolivre.", "mercadolivre"),
    ("monetizze.", "monetizze"),
    ("tiktok.", "tiktok"),
)


def infer_network(url: str | None) -> str:
    """Classifica a rede pelo host (puro, sem I/O)."""
    if not url:
        return "sem-link"
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return "invalido"
    if not host:
        return "invalido"
    host = host.lower()
    for fragment, network in HOST_NETWORK:
        if fragment in host:
            return network
    if "." not in host:
        return "invalido"
    return "outro"


def run_sync_report(db: Session, network: str | None = None) -> dict:
    """Audita produtos ativos e devolve o relatório (sem I/O)."""
    started = datetime.now(timezone.utc)
    query = db.query(Product).filter(Product.is_active.is_(True))
    products = query.all()

    checked = 0
    with_links = 0
    by_network: dict[str, int] = {}
    missing: list[dict] = []
    invalid: list[dict] = []

    for product in products:
        found = infer_network(product.affiliate_url)
        if network is not None and found != network:
            continue
        checked += 1
        by_network[found] = by_network.get(found, 0) + 1
        entry = {"product_id": product.id, "slug": product.slug}
        if found == "sem-link":
            missing.append(entry)
        elif found == "invalido":
            invalid.append(entry)
        else:
            with_links += 1

    finished = datetime.now(timezone.utc)
    return {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "network_filter": network,
        "checked": checked,
        "with_links": with_links,
        "without_links": len(missing),
        "invalid_links": len(invalid),
        "by_network": by_network,
        "missing": missing,
        "invalid": invalid,
        "live": False,
    }
