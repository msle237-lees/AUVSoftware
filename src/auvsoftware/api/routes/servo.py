"""
src/auvsoftware/api/routes/servo.py

Servo output routes.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from auvsoftware.api.deps import get_db
from auvsoftware.database.models.servo import ServoOutput
from auvsoftware.database.models.run import Run

router = APIRouter()


class ServoOutputCreate(BaseModel):
    run_id: int
    t_us: int
    seq: Optional[int] = None

    s1: int = Field(..., ge=0, le=255)
    s2: int = Field(..., ge=0, le=255)
    s3: int = Field(..., ge=0, le=255)


class ServoOutputOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    t_us: int
    seq: Optional[int]

    s1: int
    s2: int
    s3: int

    created_at: datetime
    updated_at: datetime


@router.post("", response_model=ServoOutputOut)
def create_servo_output(payload: ServoOutputCreate, db: Session = Depends(get_db)) -> ServoOutputOut:
    if db.get(Run, payload.run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    row = ServoOutput(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ServoOutputOut.model_validate(row)


@router.get("/latest", response_model=ServoOutputOut)
def get_latest_servo_output(
    run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> ServoOutputOut:
    stmt = select(ServoOutput)
    if run_id is not None:
        if db.get(Run, run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        stmt = stmt.where(ServoOutput.run_id == run_id)

    stmt = stmt.order_by(ServoOutput.t_us.desc(), ServoOutput.id.desc()).limit(1)
    row = db.execute(stmt).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No servo outputs found")
    return ServoOutputOut.model_validate(row)


@router.get("/by-run/{run_id}", response_model=list[ServoOutputOut])
def list_servo_outputs_for_run(
    run_id: int,
    t_start_us: Optional[int] = Query(None),
    t_end_us: Optional[int] = Query(None),
    limit: int = Query(5000, ge=1, le=200000),
    db: Session = Depends(get_db),
) -> list[ServoOutputOut]:
    if db.get(Run, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    stmt = select(ServoOutput).where(ServoOutput.run_id == run_id)

    if t_start_us is not None:
        stmt = stmt.where(ServoOutput.t_us >= t_start_us)
    if t_end_us is not None:
        stmt = stmt.where(ServoOutput.t_us <= t_end_us)

    stmt = stmt.order_by(ServoOutput.t_us.asc()).limit(limit)
    rows = list(db.execute(stmt).scalars().all())
    return [ServoOutputOut.model_validate(r) for r in rows]