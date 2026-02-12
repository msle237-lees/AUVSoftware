"""
Initialize the database schema for auvsoftware.

This script creates all tables defined in SQLAlchemy ORM models.
Run this once after starting the PostgreSQL container.
"""

from auvsoftware.database.engine import engine
from auvsoftware.database.base import Base

# Import ALL models so they are registered with SQLAlchemy
from auvsoftware.database.models.run import Run
from auvsoftware.database.models.imu import IMUSample
from auvsoftware.database.models.depth import DepthSample
from auvsoftware.database.models.power import PowerSample
from auvsoftware.database.models.motor import MotorOutput
from auvsoftware.database.models.servo import ServoOutput
from auvsoftware.database.models.inputs import ControlInput


def init_db() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()