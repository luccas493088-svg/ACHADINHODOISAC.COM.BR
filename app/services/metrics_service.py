from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.campaign import Campaign
from app.models.click_event import ClickEvent
from app.models.product import Product


def get_metrics_summary(db: Session, days: int = 30, top_n: int = 10) -> dict:
    """Agrega métricas de cliques para o painel de resultados."""
    total_clicks = db.query(func.count(ClickEvent.id)).scalar() or 0
    active_products = (
        db.query(func.count(Product.id))
        .filter(Product.is_active.is_(True))
        .scalar()
        or 0
    )
    active_campaigns = (
        db.query(func.count(Campaign.id))
        .filter(Campaign.is_active.is_(True))
        .scalar()
        or 0
    )

    top_rows = (
        db.query(
            Product.id,
            Product.name,
            Product.slug,
            func.count(ClickEvent.id).label("clicks"),
        )
        .join(ClickEvent, ClickEvent.product_id == Product.id)
        .group_by(Product.id, Product.name, Product.slug)
        .order_by(func.count(ClickEvent.id).desc())
        .limit(top_n)
        .all()
    )
    top_products = [
        {
            "product_id": r[0],
            "product_name": r[1],
            "product_slug": r[2],
            "clicks": r[3],
        }
        for r in top_rows
    ]

    campaign_rows = (
        db.query(
            Campaign.id,
            Campaign.name,
            Campaign.slug,
            func.count(ClickEvent.id).label("clicks"),
            func.count(func.distinct(ClickEvent.product_id)).label("products"),
        )
        .outerjoin(ClickEvent, ClickEvent.campaign_id == Campaign.id)
        .group_by(Campaign.id, Campaign.name, Campaign.slug)
        .order_by(func.count(ClickEvent.id).desc())
        .all()
    )
    by_campaign = [
        {
            "campaign_id": r[0],
            "campaign_name": r[1],
            "campaign_slug": r[2],
            "clicks": r[3],
            "products": r[4],
        }
        for r in campaign_rows
    ]

    day_rows = (
        db.query(
            func.date(ClickEvent.created_at).label("day"),
            func.count(ClickEvent.id).label("clicks"),
        )
        .group_by(func.date(ClickEvent.created_at))
        .order_by(func.date(ClickEvent.created_at).desc())
        .limit(days)
        .all()
    )
    by_day = [
        {"date": str(r[0]), "clicks": r[1]} for r in reversed(day_rows)
    ]

    return {
        "total_clicks": total_clicks,
        "active_products": active_products,
        "active_campaigns": active_campaigns,
        "top_products": top_products,
        "by_campaign": by_campaign,
        "by_day": by_day,
    }
