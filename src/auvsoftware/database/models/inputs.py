"""
src/auvsoftware/database/models/inputs.py

ORM model for pilot/controller input samples.

Each row represents one set of input values associated with a specific Run
and timestamp.
"""

from sqlalchemy import BigInteger, ForeignKey, Index, Float, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base, TimestampMixin
from auvsoftware.database.models.run import Run


class ControlInput(Base, TimestampMixin):
    """
    Pilot/controller input sample.

    Conventions:
    - t_us: monotonic timestamp in microseconds from the vehicle/controller
    - seq: optional monotonic sequence number for this stream

    Axis conventions:
    - x, y, z, yaw are continuous control axes (typically normalized)
    - s1, s2, s3 are discrete switches/buttons
    """

    __tablename__ = "control_inputs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this control input sample",
    )

    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Run ID this sample belongs to",
    )

    run: Mapped[Run] = relationship(
        "Run",
        back_populates="control_inputs",
        doc="Parent run relationship",
    )

    t_us: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="Monotonic timestamp (microseconds) from the vehicle/controller",
    )

    seq: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Optional monotonic sequence number for this stream",
    )

    # Continuous control axes
    x: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Input X axis (e.g., surge)",
    )

    y: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Input Y axis (e.g., sway)",
    )

    z: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Input Z axis (e.g., heave)",
    )

    yaw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Yaw control input",
    )

    # Discrete switches / buttons
    s1: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        doc="Switch/button S1 (0 or 1)",
    )

    s2: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        doc="Switch/button S2 (0 or 1)",
    )

    s3: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        doc="Switch/button S3 (0 or 1)",
    )


Index("ix_control_inputs_run_id_t_us", ControlInput.run_id, ControlInput.t_us)