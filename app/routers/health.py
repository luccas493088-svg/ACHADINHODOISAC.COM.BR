from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal

router = APIRouter(tags=["health"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/ready", include_in_schema=False)
def ready(db: Session = Depends(get_db)):
    """Readiness para orquestradores: 200 com banco, 503 sem banco."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "service": "isac_achadinhos_api"},
        )
    return {"status": "ready", "service": "isac_achadinhos_api"}
