# app/database/__init__.py
#
# This is the entry point for the database package.
# Importing this package gives you everything you need:
#   - The engine and session factory
#   - All models registered with Base
#   - A ready-to-call init_db() function
#
# All models are imported here so they are registered with Base.metadata
# before init_db() calls create_all(). If a model isn't imported by the
# time create_all() runs, SQLAlchemy won't know the table exists.

from auvsoftware.database.base import Base
from auvsoftware.database.engine import engine, get_session

# Importing models registers them with Base — order doesn't matter here
# but Run must be defined before the sensor models reference it via FK.
from auvsoftware.database.models.run import Run, RunStatus
from auvsoftware.database.models.depth import Depth
from auvsoftware.database.models.imu import IMU
from auvsoftware.database.models.power import Power
from auvsoftware.database.models.inputs import Inputs
from auvsoftware.database.models.motor import Motor
from auvsoftware.database.models.servo import Servo
from auvsoftware.database.models.objects import Objects
from auvsoftware.database.models.process import Process, ProcessExecution, ProcessStatus


def init_db() -> None:
    """
    Creates all tables in the database if they don't already exist.
    Safe to call multiple times — checkfirst=True means existing tables
    are left untouched.

    Call this once at application startup before doing any queries.
    """
    print("Initialising database...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("Tables ready:")
    for table_name in Base.metadata.tables:
        print(f"  ✓ {table_name}")


__all__ = [
    "init_db",
    "get_session",
    "Base",
    "Run",
    "RunStatus",
    "Depth",
    "IMU",
    "Power",
    "Inputs",
    "Motor",
    "Servo",
    "Objects",
    "Process",
    "ProcessExecution",
    "ProcessStatus",
]