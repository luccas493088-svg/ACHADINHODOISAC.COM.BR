from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base  # noqa: F401  (re-export para Alembic/autogenerate)
from app.models import (  # noqa: F401  (registra models no metadata)
    Category,
    Product,
    User,
    Campaign,
    ClickEvent,
    ConversionEvent,
    StoreProduct,
)

from app.config import Settings

settings = Settings()
engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
