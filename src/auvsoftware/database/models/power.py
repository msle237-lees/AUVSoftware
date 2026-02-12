"""
src/auvsoftware/database/models/power.py

ORM model for battery telemetry samples.

Each row represents one battery telemetry sample associated with a specific Run.
Designed for moderate-rate logging and efficient time-window queries.
"""

from sqlalchemy import BigInteger, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base, TimestampMixin
from auvsoftware.database.models.run import Run


class PowerSample(Base, TimestampMixin):
    """
    Battery telemetry sample.

    Conventions:
    - t_us: monotonic timestamp in microseconds from the vehicle/controller
    - seq: optional monotonic sequence number

    Units (recommended):
    - voltage_v: volts
    - current_a: amps
    - temp_c: degrees Celsius
    """

    __tablename__ = "power_samples"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this power telemetry sample",
    )

    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Run ID this sample belongs to",
    )

    run: Mapped[Run] = relationship(
        "Run",
        back_populates="power_samples",
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

    # -----------------------------
    # Battery pack 1
    # -----------------------------
    bat1_voltage_v: Mapped[float] = mapped_column(Float, nullable=False)
    bat1_current_a: Mapped[float] = mapped_column(Float, nullable=False)
    bat1_temp_c: Mapped[float] = mapped_column(Float, nullable=False)

    # -----------------------------
    # Battery pack 2
    # -----------------------------
    bat2_voltage_v: Mapped[float] = mapped_column(Float, nullable=False)
    bat2_current_a: Mapped[float] = mapped_column(Float, nullable=False)
    bat2_temp_c: Mapped[float] = mapped_column(Float, nullable=False)

    # -----------------------------
    # Battery pack 3
    # -----------------------------
    bat3_voltage_v: Mapped[float] = mapped_column(Float, nullable=False)
    bat3_current_a: Mapped[float] = mapped_column(Float, nullable=False)
    bat3_temp_c: Mapped[float] = mapped_column(Float, nullable=False)


Index("ix_power_samples_run_id_t_us", PowerSample.run_id, PowerSample.t_us)