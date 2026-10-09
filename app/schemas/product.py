from typing import Optional
import re
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from pydantic.networks import HttpUrl


class ProductCreate(BaseModel):
    category_id: Optional[int] = Field(None)
    campaign_id: Optional[int] = Field(None)
    name: str = Field(..., min_length=1, max_length=300)
    slug: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=2000)
    price: Decimal = Field(..., gt=0)
    old_price: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    affiliate_url: Optional[HttpUrl] = Field(None)
    badge_text: Optional[str] = Field(None, max_length=100)
    badge_type: Optional[str] = Field(None, max_length=50)
    rating: Optional[int] = Field(None, ge=0, le=5)
    is_active: bool = True
    is_featured: bool = False

    @field_validator("slug")
    @classmethod
    def slug_must_be_valid(cls, v):
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug deve conter apenas letras minúsculas, números e hífens"
            )
        return v

    @field_validator("affiliate_url")
    @classmethod
    def affiliate_url_must_be_absolute(cls, v):
        if v is not None and not str(v).startswith(("http://", "https://")):
            raise ValueError("URL de afiliado deve começar com http:// ou https://")
        return v

    @model_validator(mode="after")
    def price_must_be_higher_than_old_price(self):
        too_expensive = (
            self.old_price is not None
            and self.price is not None
            and self.old_price <= self.price
        )
        if too_expensive:
            raise ValueError("O preço antigo deve ser maior que o preço atual")
        return self

    @model_validator(mode="after")
    def url_must_be_absolute_if_provided(self):
        too_short = self.affiliate_url is not None and not str(
            self.affiliate_url
        ).startswith(("http://", "https://"))
        if too_short:
            raise ValueError("URL de afiliado deve ser uma URL absoluta")
        return self


class ProductUpdate(BaseModel):
    category_id: Optional[int] = Field(None)
    campaign_id: Optional[int] = Field(None)
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    slug: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, gt=0)
    old_price: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    affiliate_url: Optional[HttpUrl] = Field(None)
    badge_text: Optional[str] = Field(None, max_length=100)
    badge_type: Optional[str] = Field(None, max_length=50)
    rating: Optional[int] = Field(None, ge=0, le=5)
    is_active: Optional[bool] = Field(None)
    is_featured: Optional[bool] = Field(None)

    @field_validator("slug")
    @classmethod
    def slug_must_be_valid(cls, v):
        if v is not None and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug deve conter apenas letras minúsculas, números e hífens"
            )
        return v

    @field_validator("affiliate_url")
    @classmethod
    def affiliate_url_must_be_absolute(cls, v):
        if v is not None and not str(v).startswith(("http://", "https://")):
            raise ValueError("URL de afiliado deve começar com http:// ou https://")
        return v

    @model_validator(mode="after")
    def price_must_be_higher_than_old_price(self):
        too_expensive = (
            self.old_price is not None
            and self.price is not None
            and self.old_price <= self.price
        )
        if too_expensive:
            raise ValueError("O preço antigo deve ser maior que o preço atual")
        return self


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: Optional[int] = None
    campaign_id: Optional[int] = None
    name: str
    slug: str
    description: Optional[str] = None
    price: Decimal
    old_price: Optional[Decimal] = None
    image_url: Optional[str] = None
    affiliate_url: Optional[str] = None
    badge_text: Optional[str] = None
    badge_type: Optional[str] = None
    rating: Optional[int] = None
    is_active: bool
    is_featured: bool
    created_at: object
    updated_at: object


class ProductSearch(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
