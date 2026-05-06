from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Imported here to avoid circular imports (models register tables on Base).
    from app import models  # noqa: F401
    from app.db_upgrade import (
        ensure_customer_phone_column,
        ensure_orders_use_customers,
        ensure_product_prices_decimal,
    )

    Base.metadata.create_all(bind=engine)
    ensure_orders_use_customers()
    ensure_customer_phone_column()
    ensure_product_prices_decimal()
