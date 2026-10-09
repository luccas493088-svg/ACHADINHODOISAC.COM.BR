from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.jobs.import_products import run_import
from app.jobs.sync import run_sync_report
from app.limiter import limiter

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin_api(request: Request) -> dict:
    """Sessão admin para a API (403 JSON, sem redirect de HTML)."""
    user = request.session.get("user")
    if not user or user.get("role") not in ("admin", "superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao administrador",
        )
    return user


@router.post("/sync", response_model=dict)
@limiter.limit("10 per minute")
async def trigger_sync(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin_api),
    network: Optional[str] = Query(default=None, max_length=50),
):
    """Dispara o job de sincronia (dry-run, offline) e devolve o relatório."""
    _ = user
    return run_sync_report(db, network=network)


@router.post("/import", response_model=dict)
@limiter.limit("10 per minute")
async def trigger_import(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin_api),
):
    """Job manual importar_produtos (dry-run): roda conectores e grava."""
    _ = user
    return run_import(db)
