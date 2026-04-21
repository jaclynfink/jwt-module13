import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine_kwargs: dict[str, object] = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for request-scoped usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables from ORM metadata."""
    # Import models so SQLAlchemy metadata contains all tables.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
