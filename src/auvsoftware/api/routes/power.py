"""
src/auvsoftware/api/routes/power.py

Power (battery telemetry) routes.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from auvsoftware.api.deps import get_db
from auvsoftware.database.models.power import PowerSample
from auvsoftware.database.models.run import Run

router = APIRouter()


class PowerSampleCreate(BaseModel):
    run_id: int
    t_us: int
    seq: Optional[int] = None

    bat1_voltage_v: float
    bat1_current_a: float
    bat1_temp_c: float

    bat2_voltage_v: float
    bat2_current_a: float
    bat2_temp_c: float

    bat3_voltage_v: float
    bat3_current_a: float
    bat3_temp_c: float


class PowerSampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    t_us: int
    seq: Optional[int]

    bat1_voltage_v: float
    bat1_current_a: float
    bat1_temp_c: float

    bat2_voltage_v: float
    bat2_current_a: float
    bat2_temp_c: float

    bat3_voltage_v: float
    bat3_current_a: float
    bat3_temp_c: float

    created_at: datetime
    updated_at: datetime


@router.post("", response_model=PowerSampleOut)
def create_power_sample(payload: PowerSampleCreate, db: Session = Depends(get_db)) -> PowerSampleOut:
    if db.get(Run, payload.run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    row = PowerSample(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return PowerSampleOut.model_validate(row)


@router.get("/latest", response_model=PowerSampleOut)
def get_latest_power_sample(
    run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> PowerSampleOut:
    stmt = select(PowerSample)
    if run_id is not None:
        if db.get(Run, run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        stmt = stmt.where(PowerSample.run_id == run_id)

    stmt = stmt.order_by(PowerSample.t_us.desc(), PowerSample.id.desc()).limit(1)
    row = db.execute(stmt).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No power samples found")
    return PowerSampleOut.model_validate(row)


@router.get("/by-run/{run_id}", response_model=list[PowerSampleOut])
def list_power_for_run(
    run_id: int,
    t_start_us: Optional[int] = Query(None),
    t_end_us: Optional[int] = Query(None),
    limit: int = Query(5000, ge=1, le=200000),
    db: Session = Depends(get_db),
) -> list[PowerSampleOut]:
    if db.get(Run, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    stmt = select(PowerSample).where(PowerSample.run_id == run_id)

    if t_start_us is not None:
        stmt = stmt.where(PowerSample.t_us >= t_start_us)
    if t_end_us is not None:
        stmt = stmt.where(PowerSample.t_us <= t_end_us)

    stmt = stmt.order_by(PowerSample.t_us.asc()).limit(limit)
    rows = list(db.execute(stmt).scalars().all())
    return [PowerSampleOut.model_validate(r) for r in rows]