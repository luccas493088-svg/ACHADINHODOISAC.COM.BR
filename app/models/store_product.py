from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Numeric,
    Date,
    DateTime,
    func,
)

from app.db.base import Base


class StoreProduct(Base):
    """Produto da vitrine para cadastro automático futuro (Fase 8).

    Catálogo começa vazio: nada é cadastrado até os conectores live.
    Deduplicação pelo `link_afiliado` (único).
    """

    __tablename__ = "store_products"

    id = Column(Integer, primary_key=True, index=True)
    loja = Column(String(50), nullable=False, index=True)
    nome = Column(String(300), nullable=False)
    preco = Column(Numeric(precision=10, scale=2), nullable=False)
    imagem = Column(String(500), nullable=True)
    link_afiliado = Column(String(500), nullable=False, unique=True, index=True)
    data_cadastro = Column(Date, nullable=False, index=True)
    ativo = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
