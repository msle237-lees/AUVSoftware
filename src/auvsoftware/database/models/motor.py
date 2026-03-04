# models/motor.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

from sqlalchemy import SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base
from auvsoftware.database.models.mixin import SensorMixin


class Motor(SensorMixin, Base):
    __tablename__ = "motor"

    # SmallInteger is a 16-bit INT — more than enough for 0–255
    # and more memory-efficient than a full 32-bit Integer on a wide table.
    M1: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    M2: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    M3: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    M4: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    M5: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    M6: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    M7: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    M8: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="motor_readings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Motor run_id={self.run_id} M1-8=({self.M1},{self.M2},{self.M3},{self.M4},{self.M5},{self.M6},{self.M7},{self.M8})>"