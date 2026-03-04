# models/process.py
#
# Two tables work together here:
#
#   Process          — the registry of known processes in the system.
#                      A row here represents a type of process (e.g. "navigation",
#                      "depth_controller"). Created once, reused across many runs.
#
#   ProcessExecution — one row per time a process was started during a run.
#                      This is what you query to answer "what is currently running?"
#                      or "what crashed during run #12?"

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auvsoftware.database.models.run import Run

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auvsoftware.database.base import Base


class ProcessStatus(enum.Enum):
    STARTING  = "starting"   # Spawned but not yet confirmed alive
    RUNNING   = "running"    # Healthy and active
    STOPPING  = "stopping"   # Graceful shutdown in progress
    STOPPED   = "stopped"    # Exited cleanly
    CRASHED   = "crashed"    # Exited unexpectedly
    TIMEOUT   = "timeout"    # Failed to respond within expected window


class Process(Base):
    """
    Registry of all processes known to the auvsoftware system.

    A process registers itself here (or is registered at startup) with its
    name and an optional description. The same Process row is referenced by
    every ProcessExecution across all runs — you don't create a new Process
    row each time it starts, only a new ProcessExecution.
    """
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # name is unique — there is only one "navigation" process definition.
    # UniqueConstraint is also declared below for clarity, but unique=True
    # on the column itself is sufficient.
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    # Human-readable description of what this process does.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional: track which version of the process binary/module is registered.
    # Useful for debugging if behaviour changes between deployments.
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # All execution instances of this process across all runs.
    executions: Mapped[list["ProcessExecution"]] = relationship(
        "ProcessExecution",
        back_populates="process",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Process id={self.id} name={self.name!r} version={self.version!r}>"


class ProcessExecution(Base):
    """
    Tracks one instance of a process running within a specific Run.

    Query this table to answer:
      - "What processes are currently running?"     → status == RUNNING
      - "What was active during run #5?"            → run_id == 5
      - "Did anything crash in the last run?"       → status == CRASHED
      - "How long did navigation run for?"          → ended_at - started_at
    """
    __tablename__ = "process_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Which run this execution belongs to.
    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which process definition this is an instance of.
    process_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[ProcessStatus] = mapped_column(
        Enum(ProcessStatus),
        nullable=False,
        default=ProcessStatus.STARTING,
    )

    # OS-level PID — useful for correlating with system logs or sending signals.
    # Nullable because it may not be known at row-creation time.
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Lifecycle timestamps — ended_at is NULL while the process is still active.
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # If the process crashed or was stopped with an error, capture the reason.
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    run:     Mapped["Run"]     = relationship("Run",     back_populates="process_executions")  # noqa: F821
    process: Mapped["Process"] = relationship("Process", back_populates="executions")

    def __repr__(self) -> str:
        return (
            f"<ProcessExecution id={self.id} "
            f"process={self.process_id} "
            f"run={self.run_id} "
            f"status={self.status.value}>"
        )