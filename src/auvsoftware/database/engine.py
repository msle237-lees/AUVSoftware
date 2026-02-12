"""
 @file engine.py
 @brief SQLAlchemy engine creation for AUVSoftware.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .config import DATABASE_URL


def create_db_engine() -> Engine:
    """
     @brief Create and return a SQLAlchemy Engine.
     @return SQLAlchemy Engine configured for PostgreSQL.
    """
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Helps recover from dropped connections.
        future=True,
    )


# Default engine instance used by the rest of the app.
engine: Engine = create_db_engine()