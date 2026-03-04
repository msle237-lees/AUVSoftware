# models/inputs.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

from sqlalchemy import Double
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base
from auvsoftware.database.models.mixin import SensorMixin


class Inputs(SensorMixin, Base):
    __tablename__ = "inputs"

    # Translational setpoints
    x: Mapped[float] = mapped_column(Double, nullable=False)
    y: Mapped[float] = mapped_column(Double, nullable=False)
    z: Mapped[float] = mapped_column(Double, nullable=False)

    # Rotational setpoints
    roll:  Mapped[float] = mapped_column(Double, nullable=False)
    pitch: Mapped[float] = mapped_column(Double, nullable=False)
    yaw:   Mapped[float] = mapped_column(Double, nullable=False)

    # Raw servo demand values
    servo_1: Mapped[float] = mapped_column(Double, nullable=False)
    servo_2: Mapped[float] = mapped_column(Double, nullable=False)
    servo_3: Mapped[float] = mapped_column(Double, nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="input_readings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Inputs run_id={self.run_id} xyz=({self.x:.2f},{self.y:.2f},{self.z:.2f})>"