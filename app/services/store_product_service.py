from sqlalchemy.orm import Session
from app.models.store_product import StoreProduct

LOJAS = ("TikTok Shop", "Monetizze", "Mercado Livre", "AliExpress")


def list_store_products(
    db: Session,
    loja: str = "Todas",
    ordem: str = "chegada",
    limite: int = 100,
) -> list:
    """Produtos ativos da vitrine (ordem de chegada = mais antigo primeiro)."""
    query = db.query(StoreProduct).filter(StoreProduct.ativo.is_(True))
    if loja != "Todas":
        query = query.filter(StoreProduct.loja == loja)
    if ordem == "baratos":
        query = query.order_by(StoreProduct.preco.asc())
    elif ordem == "caros":
        query = query.order_by(StoreProduct.preco.desc())
    else:
        query = query.order_by(StoreProduct.data_cadastro.asc())
    return query.limit(limite).all()


def cheapest_store_products(db: Session, limite: int = 3) -> list:
    """Os mais baratos (vitrine principal)."""
    return (
        db.query(StoreProduct)
        .filter(StoreProduct.ativo.is_(True))
        .order_by(StoreProduct.preco.asc())
        .limit(limite)
        .all()
    )
