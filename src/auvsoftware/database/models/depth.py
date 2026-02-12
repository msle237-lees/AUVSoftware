"""
src/auvsoftware/database/models/depth.py

ORM model for depth samples.

Each row represents one depth sensor sample associated with a specific Run.
Designed for efficient time-window queries via (run_id, t_us).
"""

from sqlalchemy import BigInteger, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base, TimestampMixin
from auvsoftware.database.models.run import Run


class DepthSample(Base, TimestampMixin):
    """
    Depth sensor sample.

    Notes / conventions:
    - t_us: monotonic timestamp in microseconds from the vehicle/controller
    - seq: optional monotonic sequence number for this stream

    Recommended units:
    - depth_m: meters
    - pressure_pa: pascals (optional)
    - temp_c: degrees Celsius (optional)
    """

    __tablename__ = "depth_samples"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this depth sample",
    )

    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Run ID this sample belongs to",
    )

    run: Mapped[Run] = relationship(
        "Run",
        back_populates="depth_samples",
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

    depth_m: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Depth in meters",
    )

    pressure_pa: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Optional pressure in pascals",
    )

    temp_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Optional sensor temperature in degrees Celsius",
    )


Index("ix_depth_samples_run_id_t_us", DepthSample.run_id, DepthSample.t_us)