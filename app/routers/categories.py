from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from app.services.category_service import (
    get_categories,
    get_category,
    create_category,
    update_category,
    soft_delete_category,
)

router = APIRouter(prefix="/api/categories", tags=["categories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """List all active categories."""
    return get_categories(db, skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_by_id(category_id: int, db: Session = Depends(get_db)):
    """Get a category by ID."""
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return db_category


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category_route(category_in: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category."""
    return create_category(db, category_in)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category_route(
    category_id: int, category_in: CategoryUpdate, db: Session = Depends(get_db)
):
    """Update a category."""
    db_category = update_category(db, category_id, category_in)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return db_category


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Soft delete a category."""
    db_category = soft_delete_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return {"detail": "Categoria excluída com sucesso"}
