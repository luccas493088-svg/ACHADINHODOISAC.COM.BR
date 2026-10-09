from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """List categories with pagination."""
    return db.query(Category).filter(Category.is_active).offset(skip).limit(limit).all()


def get_category(db: Session, category_id: int):
    """Get a single category by ID."""
    return db.query(Category).filter(Category.id == category_id).first()


def create_category(db: Session, category_in: CategoryCreate):
    """Create a new category."""
    db_category = Category(
        name=category_in.name,
        slug=category_in.slug,
        description=category_in.description,
        is_active=category_in.is_active,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category_in: CategoryUpdate):
    """Update a category."""
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    update_data = category_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    db.commit()
    db.refresh(db_category)
    return db_category


def soft_delete_category(db: Session, category_id: int):
    """Soft delete a category by setting is_active=False."""
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    db_category.is_active = False
    db.commit()
    db.refresh(db_category)
    return db_category
