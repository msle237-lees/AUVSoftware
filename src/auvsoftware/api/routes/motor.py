"""
src/auvsoftware/api/routes/motor.py

Motor output routes.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from auvsoftware.api.deps import get_db
from auvsoftware.database.models.motor import MotorOutput
from auvsoftware.database.models.run import Run

router = APIRouter()


class MotorOutputCreate(BaseModel):
    run_id: int
    t_us: int
    seq: Optional[int] = None

    m1: int = Field(..., ge=0, le=255)
    m2: int = Field(..., ge=0, le=255)
    m3: int = Field(..., ge=0, le=255)
    m4: int = Field(..., ge=0, le=255)
    m5: int = Field(..., ge=0, le=255)
    m6: int = Field(..., ge=0, le=255)
    m7: int = Field(..., ge=0, le=255)
    m8: int = Field(..., ge=0, le=255)


class MotorOutputOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    t_us: int
    seq: Optional[int]

    m1: int
    m2: int
    m3: int
    m4: int
    m5: int
    m6: int
    m7: int
    m8: int

    created_at: datetime
    updated_at: datetime


@router.post("", response_model=MotorOutputOut)
def create_motor_output(payload: MotorOutputCreate, db: Session = Depends(get_db)) -> MotorOutputOut:
    if db.get(Run, payload.run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    row = MotorOutput(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return MotorOutputOut.model_validate(row)


@router.get("/latest", response_model=MotorOutputOut)
def get_latest_motor_output(
    run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> MotorOutputOut:
    stmt = select(MotorOutput)
    if run_id is not None:
        if db.get(Run, run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        stmt = stmt.where(MotorOutput.run_id == run_id)

    stmt = stmt.order_by(MotorOutput.t_us.desc(), MotorOutput.id.desc()).limit(1)
    row = db.execute(stmt).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No motor outputs found")
    return MotorOutputOut.model_validate(row)


@router.get("/by-run/{run_id}", response_model=list[MotorOutputOut])
def list_motor_outputs_for_run(
    run_id: int,
    t_start_us: Optional[int] = Query(None),
    t_end_us: Optional[int] = Query(None),
    limit: int = Query(5000, ge=1, le=200000),
    db: Session = Depends(get_db),
) -> list[MotorOutputOut]:
    if db.get(Run, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    stmt = select(MotorOutput).where(MotorOutput.run_id == run_id)

    if t_start_us is not None:
        stmt = stmt.where(MotorOutput.t_us >= t_start_us)
    if t_end_us is not None:
        stmt = stmt.where(MotorOutput.t_us <= t_end_us)

    stmt = stmt.order_by(MotorOutput.t_us.asc()).limit(limit)
    rows = list(db.execute(stmt).scalars().all())
    return [MotorOutputOut.model_validate(r) for r in rows]