from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    func,
)

from app.db.base import Base


class ClickEvent(Base):
    """Um clique rastreado no redirect de afiliado.

    Privacidade: IP nunca é armazenado cru — apenas hash SHA-256 com pepper.
    User-Agent e referrer são truncados.
    """

    __tablename__ = "click_events"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id = Column(
        Integer,
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ip_hash = Column(String(64), nullable=True, index=True)
    user_agent = Column(String(300), nullable=True)
    referrer = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
