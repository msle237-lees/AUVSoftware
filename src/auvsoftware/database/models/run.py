"""
@file run.py
@brief ORM model for an AUV mission / run / episode.

A Run represents a single execution of the vehicle or simulator.
All sensor streams, control outputs, and frames reference this table via run_id.
"""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from auvsoftware.database.models.imu import IMUSample
    from auvsoftware.database.models.depth import DepthSample
    from auvsoftware.database.models.power import PowerSample
    from auvsoftware.database.models.motor import MotorOutput
    from auvsoftware.database.models.servo import ServoOutput
    from auvsoftware.database.models.inputs import ControlInput

class Run(Base, TimestampMixin):
    """
    @brief Represents a single execution of the vehicle or simulator.

    A Run is the top-level container for all logged data. Each sensor, control,
    or frame table should reference Run.id as a foreign key.
    """

    __tablename__ = "runs"

    # Primary key
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this run.",
    )

    # Metadata fields
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Human-readable name for this run.",
    )

    platform: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Platform used for this run (e.g. 'hardware', 'simulation').",
    )

    vehicle: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Vehicle name or identifier (e.g. 'auv1', 'sim1').",
    )

    operator: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Name of the operator or team responsible for this run.",
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments about this run.",
    )

    config_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON string containing configuration parameters for this run.",
    )

    # Relationships
    imu_samples: Mapped[List[IMUSample]] = relationship(
        "IMUSample",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    depth_samples: Mapped[List[DepthSample]] = relationship(
        "DepthSample",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    power_samples: Mapped[List[PowerSample]] = relationship(
        "PowerSample",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    motor_outputs: Mapped[List[MotorOutput]] = relationship(
        "MotorOutput",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    servo_outputs: Mapped[List[ServoOutput]] = relationship(
        "ServoOutput",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    control_inputs: Mapped[List[ControlInput]] = relationship(
        "ControlInput",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )