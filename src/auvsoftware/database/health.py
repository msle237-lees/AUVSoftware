"""
  @file health.py
  @brief Database health check utilities.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .engine import engine as default_engine


def db_ping(engine: Engine = default_engine) -> bool:
    """
      @brief Check that the database is reachable.
      @param engine SQLAlchemy Engine to use.
      @return True if a simple query succeeds; otherwise False.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False