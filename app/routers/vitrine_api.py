from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.storefront import OrdemVitrine, StoreProductResponse
from app.services.store_product_service import (
    LOJAS,
    cheapest_store_products,
    list_store_products,
)

router = APIRouter(prefix="/api/vitrine", tags=["vitrine"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/produtos", response_model=list[StoreProductResponse])
def produtos_vitrine(
    db: Session = Depends(get_db),
    loja: str = Query(default="Todas", max_length=50),
    ordem: OrdemVitrine = Query(default="chegada"),
    limite: int = Query(default=100, ge=1, le=100),
):
    """Produtos ativos da vitrine (lidos do banco)."""
    if loja != "Todas" and loja not in LOJAS:
        raise HTTPException(status_code=422, detail="Loja desconhecida")
    return list_store_products(db, loja=loja, ordem=ordem, limite=limite)


@router.get("/destaque", response_model=list[StoreProductResponse])
def destaque_vitrine(
    db: Session = Depends(get_db),
    limite: int = Query(default=3, ge=1, le=20),
    loja: Optional[str] = Query(default=None, max_length=50),
):
    """Os mais baratos (vitrine principal), opcionalmente por loja."""
    if loja is not None and loja not in LOJAS:
        raise HTTPException(status_code=422, detail="Loja desconhecida")
    items = cheapest_store_products(db, limite=limite * 4 if loja else limite)
    if loja:
        items = [p for p in items if p.loja == loja][:limite]
    return items
