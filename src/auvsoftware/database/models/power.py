# models/power.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

from sqlalchemy import Double
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base
from auvsoftware.database.models.mixin import SensorMixin


class Power(SensorMixin, Base):
    __tablename__ = "power"

    # Three battery / bus channels
    voltage_1: Mapped[float] = mapped_column(Double, nullable=False)
    voltage_2: Mapped[float] = mapped_column(Double, nullable=False)
    voltage_3: Mapped[float] = mapped_column(Double, nullable=False)

    current_1: Mapped[float] = mapped_column(Double, nullable=False)
    current_2: Mapped[float] = mapped_column(Double, nullable=False)
    current_3: Mapped[float] = mapped_column(Double, nullable=False)

    # Temperature sensors co-located with each channel (°C)
    temp_1: Mapped[float] = mapped_column(Double, nullable=False)
    temp_2: Mapped[float] = mapped_column(Double, nullable=False)
    temp_3: Mapped[float] = mapped_column(Double, nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="power_readings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Power run_id={self.run_id} V=({self.voltage_1:.1f},{self.voltage_2:.1f},{self.voltage_3:.1f})>"