# models/imu.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

from sqlalchemy import Double
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base
from auvsoftware.database.models.mixin import SensorMixin


class IMU(SensorMixin, Base):
    __tablename__ = "imu"

    # Gyroscope — angular velocity (rad/s or deg/s depending on your hardware)
    gyro_x: Mapped[float] = mapped_column(Double, nullable=False)
    gyro_y: Mapped[float] = mapped_column(Double, nullable=False)
    gyro_z: Mapped[float] = mapped_column(Double, nullable=False)

    # Accelerometer — linear acceleration (m/s²)
    accel_x: Mapped[float] = mapped_column(Double, nullable=False)
    accel_y: Mapped[float] = mapped_column(Double, nullable=False)
    accel_z: Mapped[float] = mapped_column(Double, nullable=False)

    # Magnetometer — magnetic field (µT)
    mag_x: Mapped[float] = mapped_column(Double, nullable=False)
    mag_y: Mapped[float] = mapped_column(Double, nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="imu_readings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<IMU run_id={self.run_id} gyro=({self.gyro_x:.2f},{self.gyro_y:.2f},{self.gyro_z:.2f})>"