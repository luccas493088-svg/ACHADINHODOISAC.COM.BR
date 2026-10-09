import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import SessionLocal
from app.limiter import limiter
from app.models.click_event import ClickEvent
from app.models.product import Product

router = APIRouter(tags=["offers"])

settings = Settings()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _hash_ip(ip: str | None) -> str | None:
    """Hash SHA-256 do IP com pepper — nunca armazena o IP cru."""
    if not ip:
        return None
    return hashlib.sha256(f"{ip}:{settings.jwt_secret}".encode()).hexdigest()


@router.get("/r/{product_slug}", include_in_schema=False)
@limiter.limit("60 per minute")
def track_and_redirect(
    product_slug: str, request: Request, db: Session = Depends(get_db)
):
    """Registra o clique e redireciona para o link de afiliado.

    Fundamento da Fase 4 (rastreamento) usado pelo painel da Fase 5.
    """
    product = (
        db.query(Product)
        .filter(Product.slug == product_slug, Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Oferta não encontrada")

    event = ClickEvent(
        product_id=product.id,
        campaign_id=product.campaign_id,
        ip_hash=_hash_ip(request.client.host if request.client else None),
        user_agent=(request.headers.get("user-agent") or "")[:300] or None,
        referrer=(request.headers.get("referer") or "")[:500] or None,
    )
    db.add(event)
    db.commit()

    target = product.affiliate_url or "/"
    return RedirectResponse(url=target, status_code=302)
