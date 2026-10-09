from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category_id: int = None,
    is_featured: bool = None,
    search: str = None,
):
    """List products with pagination and optional filters."""
    query = select(Product).where(Product.is_active)

    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    if is_featured is not None:
        query = query.where(Product.is_featured == is_featured)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)

    result = db.execute(query)
    return result.scalars().all()


def get_product(db: Session, product_id: int):
    """Get a single product by ID."""
    return db.get(Product, product_id)


def create_product(db: Session, product_in: ProductCreate):
    """Create a new product."""
    db_product = Product(
        category_id=product_in.category_id,
        campaign_id=product_in.campaign_id,
        name=product_in.name,
        slug=product_in.slug,
        description=product_in.description,
        price=product_in.price,
        old_price=product_in.old_price,
        image_url=product_in.image_url,
        affiliate_url=(
            str(product_in.affiliate_url)
            if product_in.affiliate_url is not None
            else None
        ),
        badge_text=product_in.badge_text,
        badge_type=product_in.badge_type,
        rating=product_in.rating,
        is_active=product_in.is_active,
        is_featured=product_in.is_featured,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product_in: ProductUpdate):
    """Update a product."""
    db_product = db.get(Product, product_id)
    if not db_product:
        return None
    update_data = product_in.dict(exclude_unset=True)
    if update_data.get("affiliate_url") is not None:
        update_data["affiliate_url"] = str(update_data["affiliate_url"])
    for field, value in update_data.items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product


def soft_delete_product(db: Session, product_id: int):
    """Soft delete a product by setting is_active=False."""
    db_product = db.get(Product, product_id)
    if not db_product:
        return None
    db_product.is_active = False
    db.commit()
    db.refresh(db_product)
    return db_product
