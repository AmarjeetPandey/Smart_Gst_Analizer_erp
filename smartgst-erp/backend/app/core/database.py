import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import get_settings
from app.models.database import Base

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parents[2]


def _resolve_database_url(url: str) -> str:
    """Resolve SQLite URLs relative to the backend directory so uvicorn can find the same DB file regardless of cwd."""
    if not url.startswith("sqlite"):
        return url

    if url.startswith("sqlite:///./"):
        relative_path = url[len("sqlite:///./"):]
        db_path = (BASE_DIR / relative_path).resolve()
        return f"sqlite:///{db_path.as_posix()}"

    if url.startswith("sqlite:///"):
        relative_path = url[len("sqlite:///"):]
        if relative_path and not os.path.isabs(relative_path):
            db_path = (BASE_DIR / relative_path).resolve()
            return f"sqlite:///{db_path.as_posix()}"

    return url


resolved_database_url = _resolve_database_url(settings.DATABASE_URL)

# Create engine
engine = create_engine(
    resolved_database_url,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    connect_args={"check_same_thread": False} if resolved_database_url.startswith("sqlite") else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
# Reuse the shared SQLAlchemy Base from the models module so all tables register correctly.


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
