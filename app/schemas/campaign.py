from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    @field_validator("slug")
    @classmethod
    def slug_must_be_valid(cls, v):
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug deve conter apenas letras minúsculas, números e hífens"
            )
        return v

    @model_validator(mode="after")
    def period_must_be_consistent(self):
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at <= self.starts_at
        ):
            raise ValueError("A data de término deve ser posterior à data de início")
        return self


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    @field_validator("slug")
    @classmethod
    def slug_must_be_valid(cls, v):
        if v is not None and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug deve conter apenas letras minúsculas, números e hífens"
            )
        return v


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    created_at: object
    updated_at: object


class ProductClickStats(BaseModel):
    product_id: int
    product_name: str
    product_slug: str
    clicks: int


class CampaignStats(BaseModel):
    campaign_id: int
    campaign_name: str
    campaign_slug: str
    clicks: int
    products: int


class DayStats(BaseModel):
    date: str
    clicks: int


class MetricsSummary(BaseModel):
    total_clicks: int
    active_products: int
    active_campaigns: int
    top_products: list[ProductClickStats]
    by_campaign: list[CampaignStats]
    by_day: list[DayStats]
