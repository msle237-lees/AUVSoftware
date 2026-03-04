# models/depth.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

from sqlalchemy import Double
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base
from auvsoftware.database.models.mixin import SensorMixin


class Depth(SensorMixin, Base):
    __tablename__ = "depth"

    depth: Mapped[float] = mapped_column(Double, nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="depth_readings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Depth run_id={self.run_id} depth={self.depth}m>"