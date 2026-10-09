from sqlalchemy.orm import Session
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignCreate, CampaignUpdate


def get_campaigns(db: Session, skip: int = 0, limit: int = 100):
    """List campaigns with pagination."""
    return db.query(Campaign).offset(skip).limit(limit).all()


def get_active_campaigns(db: Session, skip: int = 0, limit: int = 100):
    """List only active campaigns."""
    return (
        db.query(Campaign)
        .filter(Campaign.is_active.is_(True))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_campaign(db: Session, campaign_id: int):
    """Get a single campaign by ID."""
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()


def get_campaign_by_slug(db: Session, slug: str):
    """Get a single campaign by slug."""
    return db.query(Campaign).filter(Campaign.slug == slug).first()


def create_campaign(db: Session, campaign_in: CampaignCreate):
    """Create a new campaign."""
    db_campaign = Campaign(
        name=campaign_in.name,
        slug=campaign_in.slug,
        description=campaign_in.description,
        is_active=campaign_in.is_active,
        starts_at=campaign_in.starts_at,
        ends_at=campaign_in.ends_at,
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


def update_campaign(db: Session, campaign_id: int, campaign_in: CampaignUpdate):
    """Update a campaign."""
    db_campaign = get_campaign(db, campaign_id)
    if not db_campaign:
        return None
    update_data = campaign_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_campaign, field, value)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


def soft_delete_campaign(db: Session, campaign_id: int):
    """Soft delete a campaign by setting is_active=False."""
    db_campaign = get_campaign(db, campaign_id)
    if not db_campaign:
        return None
    db_campaign.is_active = False
    db.commit()
    db.refresh(db_campaign)
    return db_campaign
