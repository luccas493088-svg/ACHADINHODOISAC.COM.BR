from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.campaign import MetricsSummary
from app.services.metrics_service import get_metrics_summary

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/summary", response_model=MetricsSummary)
def metrics_summary(
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
    top_n: int = Query(default=10, ge=1, le=50),
):
    """Painel de resultados: totais, top produtos, por campanha e por dia."""
    return get_metrics_summary(db, days=days, top_n=top_n)
