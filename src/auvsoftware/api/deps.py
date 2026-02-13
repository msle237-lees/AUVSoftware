"""
FastAPI dependencies (DB session, etc.).
"""

from collections.abc import Generator
from sqlalchemy.orm import Session

from auvsoftware.database.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session per request and ensure it closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()