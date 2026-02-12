"""
src/auvsoftware/database/models/servo.py

ORM model for servo output samples.

Each row represents one set of servo outputs (3 channels, 0–255) associated with
a specific Run and timestamp.
"""

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base, TimestampMixin
from auvsoftware.database.models.run import Run


class ServoOutput(Base, TimestampMixin):
    """
    Servo output sample.

    Conventions:
    - t_us: monotonic timestamp in microseconds from the vehicle/controller
    - seq: optional monotonic sequence number for this stream

    Channel conventions:
    - s1..s3 represent 3 servo output channels
    - values are expected to be in [0, 255]
    """

    __tablename__ = "servo_outputs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this servo output sample",
    )

    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Run ID this sample belongs to",
    )

    run: Mapped[Run] = relationship(
        "Run",
        back_populates="servo_outputs",
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

    # Servo channels (0–255)
    s1: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    s2: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    s3: Mapped[int] = mapped_column(SmallInteger, nullable=False)


Index("ix_servo_outputs_run_id_t_us", ServoOutput.run_id, ServoOutput.t_us)