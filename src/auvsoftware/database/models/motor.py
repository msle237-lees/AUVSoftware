"""
src/auvsoftware/database/models/motor.py

ORM model for motor output samples.

Each row represents one set of motor outputs (8 channels, 0-255) associated with
a specific Run and timestamp.
"""

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base, TimestampMixin
from auvsoftware.database.models.run import Run


class MotorOutput(Base, TimestampMixin):
    """
    Motor output sample.

    Conventions:
    - t_us: monotonic timestamp in microseconds from the vehicle/controller
    - seq: optional monotonic sequence number for this stream

    Channel conventions:
    - m1..m8 represent 8 motor output channels
    - values are expected to be in [0, 255]
    """

    __tablename__ = "motor_outputs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this motor output sample",
    )

    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Run ID this sample belongs to",
    )

    run: Mapped[Run] = relationship(
        "Run",
        back_populates="motor_outputs",
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

    # Motor channels (0-255)
    m1: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    m2: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    m3: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    m4: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    m5: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    m6: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    m7: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    m8: Mapped[int] = mapped_column(SmallInteger, nullable=False)


Index("ix_motor_outputs_run_id_t_us", MotorOutput.run_id, MotorOutput.t_us)