from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    Numeric,
    ForeignKey,
    func,
)

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id = Column(
        Integer,
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(300), nullable=False, index=True)
    slug = Column(String(300), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    price = Column(
        Numeric(precision=10, scale=2), nullable=False
    )
    old_price = Column(
        Numeric(precision=10, scale=2), nullable=True
    )
    image_url = Column(String(500), nullable=True)
    affiliate_url = Column(String(500), nullable=True)
    badge_text = Column(String(100), nullable=True)
    badge_type = Column(String(50), nullable=True)
    rating = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
