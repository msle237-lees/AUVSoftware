"""
src/auvsoftware/api/routes/runs.py

Run routes.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from auvsoftware.api.deps import get_db
from auvsoftware.database.models.run import Run

router = APIRouter()


class RunCreate(BaseModel):
    name: str = Field(..., max_length=128)
    platform: str = Field(..., max_length=32)
    vehicle: Optional[str] = Field(None, max_length=64)
    operator: Optional[str] = Field(None, max_length=64)
    notes: Optional[str] = None
    config_json: Optional[str] = None


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    platform: str
    vehicle: Optional[str]
    operator: Optional[str]
    notes: Optional[str]
    config_json: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.post("", response_model=RunOut)
def create_run(payload: RunCreate, db: Session = Depends(get_db)) -> RunOut:
    run = Run(**payload.model_dump())
    db.add(run)
    db.commit()
    db.refresh(run)
    return RunOut.model_validate(run)


@router.get("", response_model=list[RunOut])
def list_runs(db: Session = Depends(get_db)) -> list[RunOut]:
    stmt = select(Run).order_by(Run.id.desc())
    rows = list(db.execute(stmt).scalars().all())
    return [RunOut.model_validate(r) for r in rows]


@router.get("/latest", response_model=RunOut)
def get_latest_run(db: Session = Depends(get_db)) -> RunOut:
    stmt = select(Run).order_by(Run.id.desc()).limit(1)
    row = db.execute(stmt).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No runs found")
    return RunOut.model_validate(row)


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)) -> RunOut:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunOut.model_validate(run)