# auvsoftware/database/crud.py
#
# Convenience functions for reading and writing to the database.
# Each table has five functions:
#
#   get_all_<table>(session, run_id)      — all rows for a given run
#   get_latest_<table>(session, run_id)   — the most recent row for a given run
#   insert_<table>(session, run_id, ...)  — insert a new row and return it
#   delete_<table>(session, row_id)       — delete a single row by its id
#   delete_all_<table>(session, run_id)   — delete all rows for a given run
#
# Usage:
#   from auvsoftware.database.crud import insert_imu, get_latest_imu, get_all_imu
#
#   with get_session() as session:
#       insert_imu(session, run_id=1, gyro_x=0.1, ...)
#       row = get_latest_imu(session, run_id=1)
#       delete_imu(session, row_id=row.id)

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from auvsoftware.database.models.depth import Depth
from auvsoftware.database.models.imu import IMU
from auvsoftware.database.models.inputs import Inputs
from auvsoftware.database.models.motor import Motor
from auvsoftware.database.models.objects import Objects
from auvsoftware.database.models.power import Power
from auvsoftware.database.models.process import Process, ProcessExecution, ProcessStatus
from auvsoftware.database.models.run import Run, RunStatus
from auvsoftware.database.models.servo import Servo


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def get_all_runs(session: Session) -> list[Run]:
    """Return all runs ordered by most recent first."""
    return list(session.scalars(select(Run).order_by(Run.dt.desc())).all())


def get_latest_run(session: Session) -> Optional[Run]:
    """Return the most recently started run."""
    return session.scalars(select(Run).order_by(Run.dt.desc()).limit(1)).first()


def insert_run(
    session: Session,
    simulation: bool = False,
    notes: Optional[str] = None,
    status: RunStatus = RunStatus.PENDING,
) -> Run:
    """Create and return a new Run. Flushes so run.id is available immediately."""
    run = Run(
        dt=datetime.now(timezone.utc),
        simulation=simulation,
        status=status,
        notes=notes,
    )
    session.add(run)
    session.flush()
    return run


def delete_run(session: Session, run_id: int) -> None:
    """Delete a single run by id. Cascades to all child rows."""
    run = session.get(Run, run_id)
    if run:
        session.delete(run)
        session.flush()


def delete_all_runs(session: Session) -> None:
    """Delete every run in the database. Cascades to all child rows."""
    session.execute(delete(Run))
    session.flush()


# ---------------------------------------------------------------------------
# Depth
# ---------------------------------------------------------------------------

def get_all_depth(session: Session, run_id: int) -> list[Depth]:
    """Return all depth readings for a run ordered by timestamp."""
    return list(session.scalars(
        select(Depth).where(Depth.run_id == run_id).order_by(Depth.timestamp)
    ).all())


def get_latest_depth(session: Session, run_id: int) -> Optional[Depth]:
    """Return the most recent depth reading for a run."""
    return session.scalars(
        select(Depth).where(Depth.run_id == run_id).order_by(Depth.timestamp.desc()).limit(1)
    ).first()


def insert_depth(session: Session, run_id: int, depth: float) -> Depth:
    """Insert and return a new depth reading."""
    row = Depth(run_id=run_id, depth=depth)
    session.add(row)
    session.flush()
    return row


def delete_depth(session: Session, row_id: int) -> None:
    """Delete a single depth row by its id."""
    row = session.get(Depth, row_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_depth(session: Session, run_id: int) -> None:
    """Delete all depth readings for a given run."""
    session.execute(delete(Depth).where(Depth.run_id == run_id))
    session.flush()


# ---------------------------------------------------------------------------
# IMU
# ---------------------------------------------------------------------------

def get_all_imu(session: Session, run_id: int) -> list[IMU]:
    """Return all IMU readings for a run ordered by timestamp."""
    return list(session.scalars(
        select(IMU).where(IMU.run_id == run_id).order_by(IMU.timestamp)
    ).all())


def get_latest_imu(session: Session, run_id: int) -> Optional[IMU]:
    """Return the most recent IMU reading for a run."""
    return session.scalars(
        select(IMU).where(IMU.run_id == run_id).order_by(IMU.timestamp.desc()).limit(1)
    ).first()


def insert_imu(
    session: Session,
    run_id: int,
    gyro_x: float, gyro_y: float, gyro_z: float,
    accel_x: float, accel_y: float, accel_z: float,
    mag_x: float, mag_y: float,
) -> IMU:
    """Insert and return a new IMU reading."""
    row = IMU(
        run_id=run_id,
        gyro_x=gyro_x, gyro_y=gyro_y, gyro_z=gyro_z,
        accel_x=accel_x, accel_y=accel_y, accel_z=accel_z,
        mag_x=mag_x, mag_y=mag_y,
    )
    session.add(row)
    session.flush()
    return row


def delete_imu(session: Session, row_id: int) -> None:
    """Delete a single IMU row by its id."""
    row = session.get(IMU, row_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_imu(session: Session, run_id: int) -> None:
    """Delete all IMU readings for a given run."""
    session.execute(delete(IMU).where(IMU.run_id == run_id))
    session.flush()


# ---------------------------------------------------------------------------
# Power
# ---------------------------------------------------------------------------

def get_all_power(session: Session, run_id: int) -> list[Power]:
    """Return all power readings for a run ordered by timestamp."""
    return list(session.scalars(
        select(Power).where(Power.run_id == run_id).order_by(Power.timestamp)
    ).all())


def get_latest_power(session: Session, run_id: int) -> Optional[Power]:
    """Return the most recent power reading for a run."""
    return session.scalars(
        select(Power).where(Power.run_id == run_id).order_by(Power.timestamp.desc()).limit(1)
    ).first()


def insert_power(
    session: Session,
    run_id: int,
    voltage_1: float, voltage_2: float, voltage_3: float,
    current_1: float, current_2: float, current_3: float,
    temp_1: float,    temp_2: float,    temp_3: float,
) -> Power:
    """Insert and return a new power reading."""
    row = Power(
        run_id=run_id,
        voltage_1=voltage_1, voltage_2=voltage_2, voltage_3=voltage_3,
        current_1=current_1, current_2=current_2, current_3=current_3,
        temp_1=temp_1,       temp_2=temp_2,       temp_3=temp_3,
    )
    session.add(row)
    session.flush()
    return row


def delete_power(session: Session, row_id: int) -> None:
    """Delete a single power row by its id."""
    row = session.get(Power, row_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_power(session: Session, run_id: int) -> None:
    """Delete all power readings for a given run."""
    session.execute(delete(Power).where(Power.run_id == run_id))
    session.flush()


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def get_all_inputs(session: Session, run_id: int) -> list[Inputs]:
    """Return all input readings for a run ordered by timestamp."""
    return list(session.scalars(
        select(Inputs).where(Inputs.run_id == run_id).order_by(Inputs.timestamp)
    ).all())


def get_latest_inputs(session: Session, run_id: int) -> Optional[Inputs]:
    """Return the most recent input reading for a run."""
    return session.scalars(
        select(Inputs).where(Inputs.run_id == run_id).order_by(Inputs.timestamp.desc()).limit(1)
    ).first()


def insert_inputs(
    session: Session,
    run_id: int,
    x: float, y: float, z: float,
    roll: float, pitch: float, yaw: float,
    servo_1: float, servo_2: float, servo_3: float,
) -> Inputs:
    """Insert and return a new inputs reading."""
    row = Inputs(
        run_id=run_id,
        x=x, y=y, z=z,
        roll=roll, pitch=pitch, yaw=yaw,
        servo_1=servo_1, servo_2=servo_2, servo_3=servo_3,
    )
    session.add(row)
    session.flush()
    return row


def delete_inputs(session: Session, row_id: int) -> None:
    """Delete a single inputs row by its id."""
    row = session.get(Inputs, row_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_inputs(session: Session, run_id: int) -> None:
    """Delete all input readings for a given run."""
    session.execute(delete(Inputs).where(Inputs.run_id == run_id))
    session.flush()


# ---------------------------------------------------------------------------
# Motor
# ---------------------------------------------------------------------------

def get_all_motor(session: Session, run_id: int) -> list[Motor]:
    """Return all motor readings for a run ordered by timestamp."""
    return list(session.scalars(
        select(Motor).where(Motor.run_id == run_id).order_by(Motor.timestamp)
    ).all())


def get_latest_motor(session: Session, run_id: int) -> Optional[Motor]:
    """Return the most recent motor reading for a run."""
    return session.scalars(
        select(Motor).where(Motor.run_id == run_id).order_by(Motor.timestamp.desc()).limit(1)
    ).first()


def insert_motor(
    session: Session,
    run_id: int,
    M1: int, M2: int, M3: int, M4: int,
    M5: int, M6: int, M7: int, M8: int,
) -> Motor:
    """Insert and return a new motor reading."""
    row = Motor(
        run_id=run_id,
        M1=M1, M2=M2, M3=M3, M4=M4,
        M5=M5, M6=M6, M7=M7, M8=M8,
    )
    session.add(row)
    session.flush()
    return row


def delete_motor(session: Session, row_id: int) -> None:
    """Delete a single motor row by its id."""
    row = session.get(Motor, row_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_motor(session: Session, run_id: int) -> None:
    """Delete all motor readings for a given run."""
    session.execute(delete(Motor).where(Motor.run_id == run_id))
    session.flush()


# ---------------------------------------------------------------------------
# Servo
# ---------------------------------------------------------------------------

def get_all_servo(session: Session, run_id: int) -> list[Servo]:
    """Return all servo readings for a run ordered by timestamp."""
    return list(session.scalars(
        select(Servo).where(Servo.run_id == run_id).order_by(Servo.timestamp)
    ).all())


def get_latest_servo(session: Session, run_id: int) -> Optional[Servo]:
    """Return the most recent servo reading for a run."""
    return session.scalars(
        select(Servo).where(Servo.run_id == run_id).order_by(Servo.timestamp.desc()).limit(1)
    ).first()


def insert_servo(
    session: Session,
    run_id: int,
    S1: int, S2: int, S3: int,
) -> Servo:
    """Insert and return a new servo reading."""
    row = Servo(run_id=run_id, S1=S1, S2=S2, S3=S3)
    session.add(row)
    session.flush()
    return row


def delete_servo(session: Session, row_id: int) -> None:
    """Delete a single servo row by its id."""
    row = session.get(Servo, row_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_servo(session: Session, run_id: int) -> None:
    """Delete all servo readings for a given run."""
    session.execute(delete(Servo).where(Servo.run_id == run_id))
    session.flush()


# ---------------------------------------------------------------------------
# Objects
# ---------------------------------------------------------------------------

def get_all_objects(session: Session, run_id: int) -> list[Objects]:
    """Return all object detection readings for a run ordered by timestamp."""
    return list(session.scalars(
        select(Objects).where(Objects.run_id == run_id).order_by(Objects.timestamp)
    ).all())


def get_latest_objects(session: Session, run_id: int) -> Optional[Objects]:
    """Return the most recent object detection reading for a run."""
    return session.scalars(
        select(Objects).where(Objects.run_id == run_id).order_by(Objects.timestamp.desc()).limit(1)
    ).first()


def insert_objects(session: Session, run_id: int, detected: str) -> Objects:
    """Insert and return a new object detection reading."""
    row = Objects(run_id=run_id, detected=detected)
    session.add(row)
    session.flush()
    return row


def delete_objects(session: Session, row_id: int) -> None:
    """Delete a single objects row by its id."""
    row = session.get(Objects, row_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_objects(session: Session, run_id: int) -> None:
    """Delete all object detection readings for a given run."""
    session.execute(delete(Objects).where(Objects.run_id == run_id))
    session.flush()


# ---------------------------------------------------------------------------
# Process
# ---------------------------------------------------------------------------

def get_all_processes(session: Session) -> list[Process]:
    """Return all registered processes ordered by name."""
    return list(session.scalars(select(Process).order_by(Process.name)).all())


def get_latest_process(session: Session) -> Optional[Process]:
    """Return the most recently registered process by id."""
    return session.scalars(select(Process).order_by(Process.id.desc()).limit(1)).first()


def insert_process(
    session: Session,
    name: str,
    description: Optional[str] = None,
    version: Optional[str] = None,
) -> Process:
    """
    Register a new process. If a process with this name already exists,
    the existing row is returned instead (get-or-create pattern).
    """
    existing = session.scalars(select(Process).where(Process.name == name)).first()
    if existing:
        return existing
    row = Process(name=name, description=description, version=version)
    session.add(row)
    session.flush()
    return row


def delete_process(session: Session, process_id: int) -> None:
    """Delete a single process by its id. Cascades to all its executions."""
    row = session.get(Process, process_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_processes(session: Session) -> None:
    """Delete all registered processes. Cascades to all executions."""
    session.execute(delete(Process))
    session.flush()


# ---------------------------------------------------------------------------
# ProcessExecution
# ---------------------------------------------------------------------------

def get_all_process_executions(session: Session, run_id: int) -> list[ProcessExecution]:
    """Return all process executions for a run ordered by start time."""
    return list(session.scalars(
        select(ProcessExecution)
        .where(ProcessExecution.run_id == run_id)
        .order_by(ProcessExecution.started_at)
    ).all())


def get_latest_process_execution(session: Session, run_id: int) -> Optional[ProcessExecution]:
    """Return the most recently started process execution for a run."""
    return session.scalars(
        select(ProcessExecution)
        .where(ProcessExecution.run_id == run_id)
        .order_by(ProcessExecution.started_at.desc())
        .limit(1)
    ).first()


def insert_process_execution(
    session: Session,
    run_id: int,
    process_id: int,
    status: ProcessStatus = ProcessStatus.STARTING,
    pid: Optional[int] = None,
) -> ProcessExecution:
    """Insert and return a new process execution record."""
    row = ProcessExecution(
        run_id=run_id,
        process_id=process_id,
        status=status,
        pid=pid,
        started_at=datetime.now(timezone.utc),
    )
    session.add(row)
    session.flush()
    return row


def delete_process_execution(session: Session, row_id: int) -> None:
    """Delete a single process execution by its id."""
    row = session.get(ProcessExecution, row_id)
    if row:
        session.delete(row)
        session.flush()


def delete_all_process_executions(session: Session, run_id: int) -> None:
    """Delete all process executions for a given run."""
    session.execute(delete(ProcessExecution).where(ProcessExecution.run_id == run_id))
    session.flush()