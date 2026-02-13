"""
src/auvsoftware/api/routes/depth.py

Depth routes.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from auvsoftware.api.deps import get_db
from auvsoftware.database.models.depth import DepthSample
from auvsoftware.database.models.run import Run

router = APIRouter()


class DepthSampleCreate(BaseModel):
    run_id: int
    t_us: int
    seq: Optional[int] = None
    depth_m: float
    pressure_pa: Optional[float] = None
    temp_c: Optional[float] = None


class DepthSampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    t_us: int
    seq: Optional[int]
    depth_m: float
    pressure_pa: Optional[float]
    temp_c: Optional[float]
    created_at: datetime
    updated_at: datetime


@router.post("", response_model=DepthSampleOut)
def create_depth_sample(payload: DepthSampleCreate, db: Session = Depends(get_db)) -> DepthSampleOut:
    if db.get(Run, payload.run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    row = DepthSample(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return DepthSampleOut.model_validate(row)


@router.get("/latest", response_model=DepthSampleOut)
def get_latest_depth_sample(
    run_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> DepthSampleOut:
    stmt = select(DepthSample)
    if run_id is not None:
        if db.get(Run, run_id) is None:
            raise HTTPException(status_code=404, detail="Run not found")
        stmt = stmt.where(DepthSample.run_id == run_id)

    stmt = stmt.order_by(DepthSample.t_us.desc(), DepthSample.id.desc()).limit(1)
    row = db.execute(stmt).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No depth samples found")
    return DepthSampleOut.model_validate(row)


@router.get("/by-run/{run_id}", response_model=list[DepthSampleOut])
def list_depth_for_run(
    run_id: int,
    t_start_us: Optional[int] = Query(None),
    t_end_us: Optional[int] = Query(None),
    limit: int = Query(5000, ge=1, le=200000),
    db: Session = Depends(get_db),
) -> list[DepthSampleOut]:
    if db.get(Run, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")

    stmt = select(DepthSample).where(DepthSample.run_id == run_id)

    if t_start_us is not None:
        stmt = stmt.where(DepthSample.t_us >= t_start_us)
    if t_end_us is not None:
        stmt = stmt.where(DepthSample.t_us <= t_end_us)

    stmt = stmt.order_by(DepthSample.t_us.asc()).limit(limit)
    rows = list(db.execute(stmt).scalars().all())
    return [DepthSampleOut.model_validate(r) for r in rows]