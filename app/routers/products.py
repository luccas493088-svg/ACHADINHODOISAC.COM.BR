from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.product import Product as ProductModel
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import (
    get_products,
    get_product,
    create_product,
    update_product,
    soft_delete_product,
)

router = APIRouter(prefix="/api/products", tags=["products"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=dict)
def list_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=20, ge=1, le=100),
    category_id: Optional[int] = None,
    is_featured: Optional[bool] = None,
    search: Optional[str] = Query(default=None, max_length=100),
):
    """List products with pagination and filters."""
    if limit > 100:
        limit = 100

    items = get_products(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        is_featured=is_featured,
        search=search,
    )

    # Count total for pagination (via sessão da requisição: sem Postgres dedicado)
    total = (
        db.execute(
            select(func.count())
            .select_from(ProductModel)
            .where(ProductModel.is_active.is_(True))
        ).scalar()
        or 0
    )

    return {
        "items": [
            ProductResponse.model_validate(item).model_dump(mode="json")
            for item in items
        ],
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 0,
    }


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """Get a product by ID."""
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_product


@router.post("/", response_model=ProductResponse)
def create_product_route(product_in: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    return create_product(db, product_in)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product_route(
    product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)
):
    """Update a product."""
    db_product = update_product(db, product_id, product_in)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Soft delete a product."""
    db_product = soft_delete_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return {"detail": "Produto excluído com sucesso"}
