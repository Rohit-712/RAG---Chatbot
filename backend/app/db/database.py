"""
SQLAlchemy engine/session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# Ensure sqlite folder exists
if settings.DATABASE_URL.startswith("sqlite"):
    db_path = settings.DATABASE_URL.split("///")[-1]
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once at startup."""
    from app.models import user, chat_history  # noqa: F401 (register models)
    Base.metadata.create_all(bind=engine)
