# models/__init__.py
#
# Importing everything here means callers only need:
#   from app.database.models import Run, IMU, Motor ...
# instead of importing from each individual file.
#
# IMPORTANT: all models must be imported before Base.metadata.create_all()
# is called, so SQLAlchemy knows they exist. Importing this __init__.py
# guarantees that.

from auvsoftware.database.models.run import Run, RunStatus
from auvsoftware.database.models.depth import Depth
from auvsoftware.database.models.imu import IMU
from auvsoftware.database.models.power import Power
from auvsoftware.database.models.inputs import Inputs
from auvsoftware.database.models.motor import Motor
from auvsoftware.database.models.servo import Servo
from auvsoftware.database.models.objects import Objects
from auvsoftware.database.models.process import Process, ProcessExecution, ProcessStatus

__all__ = [
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