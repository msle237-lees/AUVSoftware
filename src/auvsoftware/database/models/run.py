# models/run.py
#
# The Run table is the "parent" of everything else.
# Every sensor reading, motor command, etc. is tied to a specific Run
# via a foreign key. This lets you query "give me all IMU readings from run #5".
#
# Extra tracking fields added:
#   status      — where in its lifecycle the run is (pending → running → done/failed)
#   end_dt      — when the run finished (None while still running)
#   notes       — free-text field for operators to annotate a run
#   created_at  — when the row was inserted (auto-set by the DB)

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.depth import Depth
    from auvsoftware.database.models.imu import IMU
    from auvsoftware.database.models.power import Power
    from auvsoftware.database.models.inputs import Inputs
    from auvsoftware.database.models.motor import Motor
    from auvsoftware.database.models.servo import Servo
    from auvsoftware.database.models.objects import Objects
    from auvsoftware.database.models.process import ProcessExecution

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base


class RunStatus(enum.Enum):
    """
    Python Enum → stored as a PostgreSQL ENUM type.
    SQLAlchemy keeps these in sync automatically.
    """
    PENDING   = "pending"    # Initialised but not yet started
    RUNNING   = "running"    # Actively collecting data
    COMPLETED = "completed"  # Finished cleanly
    FAILED    = "failed"     # Aborted due to an error
    ABORTED   = "aborted"    # Manually cancelled


class Run(Base):
    """
    One row = one complete vehicle run (real or simulated).

    The `__tablename__` string is what the table is called in PostgreSQL.
    Every model needs one.
    """
    __tablename__ = "runs"

    # --- Primary Key ---
    # Mapped[int] is a type hint that tells SQLAlchemy (and your IDE) what
    # Python type this column holds. mapped_column() defines the DB column.
    # Integer primary keys with autoincrement are the standard PK pattern.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Core fields ---
    # DateTime(timezone=True) stores timezone-aware timestamps in PostgreSQL.
    # default=... sets the value in Python when you create a new Run().
    # server_default= would set it in SQL — we use default= here so the
    # value is available immediately without a round-trip to the DB.
    dt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    simulation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- Run lifecycle tracking ---
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus),
        nullable=False,
        default=RunStatus.PENDING,
    )
    end_dt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,   # NULL while the run is still active
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # func.now() calls PostgreSQL's NOW() — the DB sets this automatically
    # on INSERT. Good for audit trails since it's the DB clock, not the app clock.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    # relationship() tells SQLAlchemy "when I load a Run, also let me access
    # run.depth_readings as a Python list". It does NOT add any columns —
    # the foreign key lives on the *child* table.
    #
    # back_populates="run" means the child model has a matching relationship
    # called `run` that points back here. They stay in sync automatically.
    #
    # cascade="all, delete-orphan" means: if you delete a Run, also delete
    # all its related rows. Without this, the DB would raise a FK violation.
    depth_readings:   Mapped[list["Depth"]]   = relationship("Depth",   back_populates="run", cascade="all, delete-orphan")
    imu_readings:     Mapped[list["IMU"]]     = relationship("IMU",     back_populates="run", cascade="all, delete-orphan")
    power_readings:   Mapped[list["Power"]]   = relationship("Power",   back_populates="run", cascade="all, delete-orphan")
    input_readings:   Mapped[list["Inputs"]]  = relationship("Inputs",  back_populates="run", cascade="all, delete-orphan")
    motor_readings:   Mapped[list["Motor"]]   = relationship("Motor",   back_populates="run", cascade="all, delete-orphan")
    servo_readings:   Mapped[list["Servo"]]   = relationship("Servo",   back_populates="run", cascade="all, delete-orphan")
    object_readings:     Mapped[list["Objects"]]          = relationship("Objects",          back_populates="run", cascade="all, delete-orphan")
    process_executions:  Mapped[list["ProcessExecution"]] = relationship("ProcessExecution", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        # __repr__ is what Python prints when you inspect an object.
        # Very helpful when debugging in a REPL.
        return f"<Run id={self.id} status={self.status.value} simulation={self.simulation}>"