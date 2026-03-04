# models/mixin.py
#
# A Mixin is a plain Python class (no Base) that contributes columns.
# Any model that inherits from it gets those columns automatically.
# This avoids copy-pasting id / run_id / timestamp into every table.

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column


class SensorMixin:
    """Shared columns for every sensor / telemetry table."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # BigInteger for the PK because telemetry tables can grow very large.

    # ForeignKey("runs.id") references the `id` column of the `runs` table.
    # ondelete="CASCADE" instructs PostgreSQL to automatically delete child
    # rows when the parent Run is deleted — mirrors the ORM-level cascade.
    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Index speeds up "give me all rows for run #5" queries
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )