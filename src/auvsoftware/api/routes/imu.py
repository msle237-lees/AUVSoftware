"""
src/auvsoftware/api/routes/imu.py

IMU routes.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from auvsoftware.api.deps import get_db
from auvsoftware.database.models.imu import IMUSample
from auvsoftware.database.models.run import Run

router = APIRouter()


class IMUSampleCreate(BaseModel):
    run_id: int
    t_us: int
    seq: Optional[int] = None
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    mx: float
    my: float
    mz: float
    temp_c: Optional[float] = None


class IMUSampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    t_us: int
    seq: Optional[int]
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    mx: float
    my: float
    mz: float
    temp_c: Optional[float]
    created_at: datetime
    updated_at: datetime


@router.post("", response_model=IMUSampleOut)
def create_imu_sample(payload: IMUSampleCreate, db: Session = Depends(get_db)) -> IMUSampleOut:
    if db.get(Run, payload.run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    row = IMUSample(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return IMUSampleOut.model_validate(row)


@router.get("/latest", response_model=IMUSampleOut)
def get_latest_imu_sample(
    run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> IMUSampleOut:
    """
    Get the latest IMU sample (globally or within a run).

    Latest is defined as the greatest (t_us, id) for the selection.
    """
    stmt = select(IMUSample)
    if run_id is not None:
        if db.get(Run, run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        stmt = stmt.where(IMUSample.run_id == run_id)

    stmt = stmt.order_by(IMUSample.t_us.desc(), IMUSample.id.desc()).limit(1)
    row = db.execute(stmt).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No IMU samples found")
    return IMUSampleOut.model_validate(row)


@router.get("/by-run/{run_id}", response_model=list[IMUSampleOut])
def list_imu_for_run(
    run_id: int,
    t_start_us: Optional[int] = Query(None),
    t_end_us: Optional[int] = Query(None),
    limit: int = Query(5000, ge=1, le=200000),
    db: Session = Depends(get_db),
) -> list[IMUSampleOut]:
    if db.get(Run, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    stmt = select(IMUSample).where(IMUSample.run_id == run_id)

    if t_start_us is not None:
        stmt = stmt.where(IMUSample.t_us >= t_start_us)
    if t_end_us is not None:
        stmt = stmt.where(IMUSample.t_us <= t_end_us)

    stmt = stmt.order_by(IMUSample.t_us.asc()).limit(limit)
    rows = list(db.execute(stmt).scalars().all())
    return [IMUSampleOut.model_validate(r) for r in rows]