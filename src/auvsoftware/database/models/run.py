"""
@file run.py
@brief ORM model for an AUV mission / run / episode.

A Run represents a single execution of the vehicle or simulator.
All sensor streams, control outputs, and frames reference this table via run_id.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base, TimestampMixin

class Run(Base, TimestampMixin):
    """
    @brief Represents a single execution of the vehicle or simulator.

    A Run is the top-level container for all logged data. Each sensor, control, or frame table should reference Run.id as a foreign key.
    """

    __tablename__ = "runs"

    # Primary key
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this run."
    )

    # Metadata fields
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Human-readable name for this run."
    )

    platform: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Platform used for this run (e.g. 'simulator', 'bluefin-9')."
    )

    vehicle: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Vehicle name or identifier (e.g. 'auv1', 'sim1')."
    )

    operator: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Name of the operator or team responsible for this run."
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes or comments about this run."
    )

    # Optional configuration or parameters used for this run, stored as JSON string
    config_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON string containing configuration parameters for this run."
    )

    # Relationships (defined later)
    # These are placeholders; actual relationships should be added once
    # the corresponding ORM models exist.
    #
    # imu_samples = relationship("IMUSample", back_populates="run")
    # depth_samples = relationship("DepthSample", back_populates="run")
    # motor_outputs = relationship("MotorOutput", back_populates="run")
    # rgb_frames = relationship("RGBFrame", back_populates="run")