from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class WebhookResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="created=criado | duplicate=duplicado")
    event_id: Optional[int] = None
    network: str


class ConversionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    network: str
    external_id: str
    product_id: Optional[int] = None
    campaign_id: Optional[int] = None
    amount: Optional[Decimal] = None
    currency: str
    status: str
