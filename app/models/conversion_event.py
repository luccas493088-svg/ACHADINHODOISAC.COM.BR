from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Text,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    func,
)

from app.db.base import Base


class ConversionEvent(Base):
    """Conversão avisada via webhook por uma rede de afiliados.

    Idempotência: (network, external_id) é único — reenvios retornam
    `duplicate` sem duplicar. `payload` guarda o JSON cru para auditoria.
    """

    __tablename__ = "conversion_events"

    id = Column(Integer, primary_key=True, index=True)
    network = Column(String(50), nullable=False, index=True)
    external_id = Column(String(200), nullable=False, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id = Column(
        Integer,
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount = Column(Numeric(precision=10, scale=2), nullable=True)
    currency = Column(String(10), nullable=False, default="BRL")
    status = Column(String(50), nullable=False, default="received")
    payload = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("network", "external_id", name="uq_network_external"),
    )
