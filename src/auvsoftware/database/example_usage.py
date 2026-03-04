# example_usage.py
#
# A worked example showing the full lifecycle of a Run with sensor data
# and process tracking.
#
# Usage:
#   python example_usage.py

import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from auvsoftware.database import (
    get_session, init_db,
    Depth, IMU, Inputs, Motor, Objects, Power, Run, RunStatus, Servo,
    Process, ProcessExecution, ProcessStatus,
)


# ---------------------------------------------------------------------------
# Helper — dynamic process registration
# ---------------------------------------------------------------------------
def get_or_register_process(
    session: Session,
    name: str,
    version: Optional[str] = None,
    description: Optional[str] = None,
) -> Process:
    """
    Fetch a process by name if it already exists, otherwise create it.
    This is the standard pattern for dynamic registration — processes
    register themselves at runtime without any hardcoded list.
    """
    process = session.scalars(select(Process).where(Process.name == name)).first()

    if process is None:
        process = Process(name=name, version=version, description=description)
        session.add(process)
        session.flush()  # Populate process.id without committing
        print(f"  Registered new process: {name!r}")
    else:
        print(f"  Found existing process: {name!r} (id={process.id})")

    return process


# ---------------------------------------------------------------------------
# 1. CREATE — start a new run, register processes, log sensor readings
# ---------------------------------------------------------------------------
def create_example_run() -> int:
    """
    Opens a session, creates a Run + process executions + sensor rows,
    commits, and returns the run id.
    """
    with get_session() as session:

        # Create the parent Run object (in Python — not in the DB yet)
        run = Run(
            dt=datetime.now(timezone.utc),
            simulation=True,
            status=RunStatus.RUNNING,
            notes="Example run created by example_usage.py",
        )
        session.add(run)

        # flush() sends the INSERT to the DB within the current transaction
        # so that run.id is populated by the autoincrement — but does NOT commit.
        # We need run.id before we can attach child rows.
        session.flush()
        print(f"Created run with id={run.id}")

        # --- Register and start processes ---
        # Each process registers itself dynamically. If it's been seen before
        # the existing row is returned; otherwise a new one is created.
        print("\nRegistering processes...")
        nav     = get_or_register_process(session, "navigation",       version="1.0.0", description="Waypoint navigation controller")
        depth_c = get_or_register_process(session, "depth_controller", version="1.0.0", description="PID controller for depth hold")
        vision  = get_or_register_process(session, "vision",           version="2.1.0", description="Object detection pipeline")

        # Create an execution record for each process in this run.
        # os.getpid() captures the real PID — in production each process
        # would pass its own PID when it registers itself.
        nav_exe = ProcessExecution(
            run_id=run.id, process_id=nav.id,
            status=ProcessStatus.RUNNING, pid=os.getpid(),
        )
        depth_exe = ProcessExecution(
            run_id=run.id, process_id=depth_c.id,
            status=ProcessStatus.RUNNING, pid=os.getpid() + 1,
        )
        vision_exe = ProcessExecution(
            run_id=run.id, process_id=vision.id,
            status=ProcessStatus.STARTING, pid=None,  # Not alive yet
        )
        session.add_all([nav_exe, depth_exe, vision_exe])
        session.flush()

        # --- Log sensor readings ---
        depth_row = Depth(run_id=run.id, depth=12.4)
        imu_row = IMU(
            run_id=run.id,
            gyro_x=0.01, gyro_y=-0.02, gyro_z=0.00,
            accel_x=0.0, accel_y=0.0,  accel_z=9.81,
            mag_x=23.5,  mag_y=-14.2,
        )
        power_row = Power(
            run_id=run.id,
            voltage_1=16.2, voltage_2=16.1, voltage_3=16.0,
            current_1=4.2,  current_2=3.8,  current_3=4.0,
            temp_1=32.1,    temp_2=31.8,    temp_3=33.0,
        )
        inputs_row = Inputs(
            run_id=run.id,
            x=0.5, y=0.0, z=-0.2,
            roll=0.0, pitch=0.05, yaw=0.1,
            servo_1=128.0, servo_2=128.0, servo_3=128.0,
        )
        motor_row = Motor(
            run_id=run.id,
            M1=140, M2=140, M3=140, M4=140,
            M5=128, M6=128, M7=100, M8=100,
        )
        servo_row   = Servo(run_id=run.id, S1=128, S2=128, S3=128)
        objects_row = Objects(run_id=run.id, detected="buoy:0.92,pipe:0.78")

        session.add_all([depth_row, imu_row, power_row, inputs_row, motor_row, servo_row, objects_row])
        session.commit()
        print("\nCommitted all sensor rows and process executions.")

        return run.id


# ---------------------------------------------------------------------------
# 2. READ — load a run and its related data
# ---------------------------------------------------------------------------
def read_run(run_id: int) -> None:
    with get_session() as session:

        # session.get() fetches a row by primary key — the simplest query.
        run = session.get(Run, run_id)

        if run is None:
            print(f"No run found with id={run_id}")
            return

        print(f"\n--- Run #{run.id} ---")
        print(f"  Status:     {run.status.value}")
        print(f"  Simulation: {run.simulation}")
        print(f"  Started:    {run.dt}")
        print(f"  Notes:      {run.notes}")

        # Accessing run.process_executions triggers a SELECT automatically.
        # SQLAlchemy calls this "lazy loading" — it fetches child rows only
        # when you actually touch the attribute.
        print(f"\n  Process executions ({len(run.process_executions)}):")
        for exe in run.process_executions:
            proc_name = exe.process.name  # Lazy-loads the related Process row
            print(f"    [{exe.status.value:10}] {proc_name} (pid={exe.pid})")

        print(f"\n  Depth readings ({len(run.depth_readings)}):")
        for d in run.depth_readings:
            print(f"    {d}")

        print(f"\n  IMU readings ({len(run.imu_readings)}):")
        for i in run.imu_readings:
            print(f"    {i}")

        print(f"\n  Motor readings ({len(run.motor_readings)}):")
        for m in run.motor_readings:
            print(f"    {m}")


# ---------------------------------------------------------------------------
# 3. UPDATE — simulate vision coming online, then complete the run
# ---------------------------------------------------------------------------
def update_processes_and_complete(run_id: int) -> None:
    with get_session() as session:

        # Find the vision execution for this run
        stmt = (
            select(ProcessExecution)
            .join(Process)
            .where(ProcessExecution.run_id == run_id)
            .where(Process.name == "vision")
        )
        vision_exe = session.scalars(stmt).first()

        # Explicit is not None check so Pylance can narrow the Optional type
        if vision_exe is not None:
            vision_exe.status = ProcessStatus.RUNNING
            vision_exe.pid    = os.getpid() + 2
            print(f"\nVision process is now RUNNING (pid={vision_exe.pid})")

        # Mark all running processes as stopped
        stmt = (
            select(ProcessExecution)
            .where(ProcessExecution.run_id == run_id)
            .where(ProcessExecution.status == ProcessStatus.RUNNING)
        )
        active = session.scalars(stmt).all()
        for exe in active:
            exe.status   = ProcessStatus.STOPPED
            exe.ended_at = datetime.now(timezone.utc)
        print(f"Stopped {len(active)} process(es).")

        # Mark the run itself as completed
        run = session.get(Run, run_id)
        if run is not None:
            run.status = RunStatus.COMPLETED
            run.end_dt = datetime.now(timezone.utc)

        session.commit()
        print(f"Run {run_id} marked as COMPLETED.")


# ---------------------------------------------------------------------------
# 4. QUERY — useful cross-run queries
# ---------------------------------------------------------------------------
def query_examples() -> None:
    with get_session() as session:

        # All currently running processes across all runs
        stmt = select(ProcessExecution).where(ProcessExecution.status == ProcessStatus.RUNNING)
        active = session.scalars(stmt).all()
        print(f"\nCurrently running processes: {active}")

        # All processes that have ever crashed
        stmt = select(ProcessExecution).where(ProcessExecution.status == ProcessStatus.CRASHED)
        crashed = session.scalars(stmt).all()
        print(f"Crashed processes: {crashed}")

        # All simulation runs
        stmt = select(Run).where(Run.simulation == True)  # noqa: E712
        sim_runs = session.scalars(stmt).all()
        print(f"Simulation runs: {sim_runs}")

        # Depth readings deeper than 10m across all runs
        stmt = select(Depth).where(Depth.depth > 10.0)
        deep = session.scalars(stmt).all()
        print(f"Depth readings > 10m: {deep}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()                               # Creates any missing tables
    run_id = create_example_run()
    read_run(run_id)
    update_processes_and_complete(run_id)
    read_run(run_id)                        # Read again to confirm changes
    query_examples()