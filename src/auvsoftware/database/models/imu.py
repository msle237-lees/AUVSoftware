"""
  @file imu.py
  @brief ORM model for IMU + Magnetometer samples.
 
  Each row represents one IMU sample associated with a specific Run.
  Designed for high-rate insertion and time-aligned querying via (run_id, t_us).
"""

from sqlalchemy import BigInteger, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base, TimestampMixin
from auvsoftware.database.models.run import Run


class IMUSample(Base, TimestampMixin):
    """
    
      @brief Represents a single IMU + magnetometer sample.
     
      Recommended conventions:
      - t_us is a monotonic timestamp in microseconds from the vehicle/controller.
      - recv_ts is optional; use created_at/updated_at (TimestampMixin) for server timing.
     
      Units (recommended):
      - accel (ax, ay, az): m/s^2
      - gyro  (gx, gy, gz): rad/s
      - mag   (mx, my, mz): microtesla (uT) or gauss (document which you use)
     
    """

    __tablename__ = "imu_samples"

    # -----------------------------
    # Primary Key
    # -----------------------------
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique identifier for this IMU sample",
    )

    # -----------------------------
    # Foreign Key to runs
    # -----------------------------
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Run ID this sample belongs to",
    )

    run: Mapped[Run] = relationship(
        "Run",
        back_populates="imu_samples",
        doc="Parent run relationship",
    )

    # -----------------------------
    # Time / sequencing
    # -----------------------------
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
    # IMU: accelerometer (m/s^2)
    # -----------------------------
    ax: Mapped[float] = mapped_column(Float, nullable=False, doc="Acceleration X (m/s^2)")
    ay: Mapped[float] = mapped_column(Float, nullable=False, doc="Acceleration Y (m/s^2)")
    az: Mapped[float] = mapped_column(Float, nullable=False, doc="Acceleration Z (m/s^2)")

    # -----------------------------
    # IMU: gyroscope (rad/s)
    # -----------------------------
    gx: Mapped[float] = mapped_column(Float, nullable=False, doc="Angular velocity X (rad/s)")
    gy: Mapped[float] = mapped_column(Float, nullable=False, doc="Angular velocity Y (rad/s)")
    gz: Mapped[float] = mapped_column(Float, nullable=False, doc="Angular velocity Z (rad/s)")

    # -----------------------------
    # Magnetometer (uT or gauss)
    # -----------------------------
    mx: Mapped[float] = mapped_column(Float, nullable=False, doc="Magnetic field X")
    my: Mapped[float] = mapped_column(Float, nullable=False, doc="Magnetic field Y")
    mz: Mapped[float] = mapped_column(Float, nullable=False, doc="Magnetic field Z")

    # -----------------------------
    # Optional sensor temperature
    # -----------------------------
    temp_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Optional IMU temperature (°C)",
    )


# Composite index for fast time-window queries within a run.
Index("ix_imu_samples_run_id_t_us", IMUSample.run_id, IMUSample.t_us)
