"""
  @file session.py
  @brief SQLAlchemy session factory and FastAPI dependency helpers.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from .engine import engine

# Factory for creating DB sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
      @brief FastAPI-friendly DB session dependency.
     
      Usage (FastAPI):
      @code
      from fastapi import Depends
      from sqlalchemy.orm import Session
      from auvsoftware.database.session import get_db
     
      @app.get("/example")
      def example(db: Session = Depends(get_db)):
          ...
      @endcode
     
      @return Yields a SQLAlchemy Session and ensures it is closed.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()