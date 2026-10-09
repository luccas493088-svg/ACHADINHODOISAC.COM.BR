from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
)
from app.services.campaign_service import (
    get_campaigns,
    get_campaign,
    create_campaign,
    update_campaign,
    soft_delete_campaign,
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[CampaignResponse])
def list_campaigns(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """List campaigns with pagination."""
    return get_campaigns(db, skip=skip, limit=limit)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign_by_id(campaign_id: int, db: Session = Depends(get_db)):
    """Get a campaign by ID."""
    db_campaign = get_campaign(db, campaign_id)
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return db_campaign


@router.post("/", response_model=CampaignResponse, status_code=201)
def create_campaign_route(campaign_in: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new campaign."""
    return create_campaign(db, campaign_in)


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign_route(
    campaign_id: int, campaign_in: CampaignUpdate, db: Session = Depends(get_db)
):
    """Update a campaign."""
    db_campaign = update_campaign(db, campaign_id, campaign_in)
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return db_campaign


@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Soft delete a campaign."""
    db_campaign = soft_delete_campaign(db, campaign_id)
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return {"detail": "Campanha excluída com sucesso"}
