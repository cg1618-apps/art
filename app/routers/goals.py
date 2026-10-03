"""Goals: the roadmap's levels, each with its stages."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Goal, Stage
from app.services import goals, stages

router = APIRouter(prefix="/api/goals", tags=["Goals"])


def stage_summary_fields(row: Stage, number: int) -> dict:
    return {
        "id": row.id,
        "number": number,
        "display_name": row.display_name,
        "name_cn": row.name_cn,
        "name_en": row.name_en,
        "name_alt": row.name_alt,
        "position": row.position,
        "description": row.description,
        "test": row.test,
        "status": row.status,
        "passed_on": row.passed_on,
    }


def _response(row: Goal, numbers: dict[int, int]) -> schemas.GoalResponse:
    return schemas.GoalResponse(
        id=row.id,
        code=row.code,
        display_name=row.display_name,
        name_cn=row.name_cn,
        name_en=row.name_en,
        name_alt=row.name_alt,
        position=row.position,
        description=row.description,
        test=row.test,
        status=row.status,
        achieved_on=row.achieved_on,
        remark=row.remark,
        stages=[
            schemas.StageSummary(**stage_summary_fields(stage, numbers[stage.id]))
            for stage in row.stages
        ],
    )


@router.get("", response_model=list[schemas.GoalResponse])
def list_goals(db: Session = Depends(get_db)):
    """The roadmap: a bare array in position order, each goal with its stages
    numbered across the whole roadmap."""
    numbers = stages.numbers(db)
    return [_response(row, numbers) for row in goals.listed(db)]


@router.get("/{goal_id}", response_model=schemas.GoalResponse)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    return _response(goals.get(db, goal_id), stages.numbers(db))


@router.post("", response_model=schemas.GoalResponse, status_code=201)
def create_goal(payload: schemas.GoalCreate, db: Session = Depends(get_db)):
    return _response(goals.create(db, payload), stages.numbers(db))


@router.patch("/{goal_id}", response_model=schemas.GoalResponse)
def update_goal(goal_id: int, payload: schemas.GoalUpdate, db: Session = Depends(get_db)):
    return _response(goals.update(db, goal_id, payload), stages.numbers(db))


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """409 `{detail, stages: n}` while the goal still has stages, and
    `{detail, records: n}` while test records name it."""
    goals.delete(db, goal_id)
    return Response(status_code=204)
