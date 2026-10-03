"""Stages: one step of a level, with its goal, number and resources."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Stage
from app.routers.common import goal_ref, resource_list
from app.routers.goals import stage_summary_fields
from app.services import stages

router = APIRouter(prefix="/api/stages", tags=["Stages"])


def _response(db: Session, row: Stage) -> schemas.StageResponse:
    return schemas.StageResponse(
        **stage_summary_fields(row, stages.numbers(db)[row.id]),
        goal=goal_ref(row.goal),
        remark=row.remark,
        resources=resource_list(row.resources),
    )


@router.get("/{stage_id}", response_model=schemas.StageResponse)
def get_stage(stage_id: int, db: Session = Depends(get_db)):
    return _response(db, stages.get(db, stage_id))


@router.post("", response_model=schemas.StageResponse, status_code=201)
def create_stage(payload: schemas.StageCreate, db: Session = Depends(get_db)):
    return _response(db, stages.create(db, payload))


@router.patch("/{stage_id}", response_model=schemas.StageResponse)
def update_stage(stage_id: int, payload: schemas.StageUpdate, db: Session = Depends(get_db)):
    return _response(db, stages.update(db, stage_id, payload))


@router.delete("/{stage_id}", status_code=204)
def delete_stage(stage_id: int, db: Session = Depends(get_db)):
    """Its resources go with it; its exercises stay, with no stage. 409
    `{detail, records}` while test records name it."""
    stages.delete(db, stage_id)
    return Response(status_code=204)
