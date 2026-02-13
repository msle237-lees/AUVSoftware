"""
src/auvsoftware/api/routes/inputs.py

Control input routes.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from auvsoftware.api.deps import get_db
from auvsoftware.database.models.inputs import ControlInput
from auvsoftware.database.models.run import Run

router = APIRouter()


class ControlInputCreate(BaseModel):
    run_id: int
    t_us: int
    seq: Optional[int] = None

    x: float
    y: float
    z: float
    yaw: float

    s1: int
    s2: int
    s3: int


class ControlInputOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    t_us: int
    seq: Optional[int]

    x: float
    y: float
    z: float
    yaw: float

    s1: int
    s2: int
    s3: int

    created_at: datetime
    updated_at: datetime


@router.post("", response_model=ControlInputOut)
def create_control_input(payload: ControlInputCreate, db: Session = Depends(get_db)) -> ControlInputOut:
    if db.get(Run, payload.run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    row = ControlInput(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ControlInputOut.model_validate(row)


@router.get("/latest", response_model=ControlInputOut)
def get_latest_control_input(
    run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> ControlInputOut:
    stmt = select(ControlInput)
    if run_id is not None:
        if db.get(Run, run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        stmt = stmt.where(ControlInput.run_id == run_id)

    stmt = stmt.order_by(ControlInput.t_us.desc(), ControlInput.id.desc()).limit(1)
    row = db.execute(stmt).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No control inputs found")
    return ControlInputOut.model_validate(row)


@router.get("/by-run/{run_id}", response_model=list[ControlInputOut])
def list_control_inputs_for_run(
    run_id: int,
    t_start_us: Optional[int] = Query(None),
    t_end_us: Optional[int] = Query(None),
    limit: int = Query(5000, ge=1, le=200000),
    db: Session = Depends(get_db),
) -> list[ControlInputOut]:
    if db.get(Run, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    stmt = select(ControlInput).where(ControlInput.run_id == run_id)

    if t_start_us is not None:
        stmt = stmt.where(ControlInput.t_us >= t_start_us)
    if t_end_us is not None:
        stmt = stmt.where(ControlInput.t_us <= t_end_us)

    stmt = stmt.order_by(ControlInput.t_us.asc()).limit(limit)
    rows = list(db.execute(stmt).scalars().all())
    return [ControlInputOut.model_validate(r) for r in rows]