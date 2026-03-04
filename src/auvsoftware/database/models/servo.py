# models/servo.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

from sqlalchemy import SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base
from auvsoftware.database.models.mixin import SensorMixin


class Servo(SensorMixin, Base):
    __tablename__ = "servo"

    S1: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    S2: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    S3: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="servo_readings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Servo run_id={self.run_id} S1-3=({self.S1},{self.S2},{self.S3})>"