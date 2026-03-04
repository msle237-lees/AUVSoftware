# models/objects.py

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base
from auvsoftware.database.models.mixin import SensorMixin


class Objects(SensorMixin, Base):
    __tablename__ = "objects"

    # String(512) maps to VARCHAR(512) in PostgreSQL.
    # Could be JSON, a label name, a CSV of detections — keep it flexible.
    detected: Mapped[str] = mapped_column(String(512), nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="object_readings")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Objects run_id={self.run_id} detected={self.detected!r}>"