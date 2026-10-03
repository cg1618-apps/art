"""Drills: one prescribed way of practising an exercise. The list across
every exercise in roadmap order, one drill, and the writes. Each exercise's
own drills also come with it (`GET /api/exercises/{id}`)."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Drill
from app.routers.common import option_ref, resource_list, stage_ref
from app.services import drills, records, stages

router = APIRouter(prefix="/api/drills", tags=["Drills"])


def drill_response(row: Drill) -> schemas.DrillResponse:
    return schemas.DrillResponse(
        id=row.id,
        exercise=schemas.ExerciseRef(id=row.exercise.id, display_name=row.exercise.display_name),
        display_name=row.display_name,
        name=row.name,
        source=option_ref(row.source),
        source_links=resource_list(row.source_links),
        resources=resource_list(row.resources),
        instructions=row.instructions,
        unit=row.unit,
        target=row.target,
        suggested_minutes=row.suggested_minutes,
        frequency=row.frequency,
        remark=row.remark,
        position=row.position,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def drill_summary(row: Drill, numbers: dict, totals: dict) -> schemas.DrillSummary:
    record_count, total_minutes = totals.get(row.id, (0, 0))
    exercise = row.exercise
    return schemas.DrillSummary(
        id=row.id,
        display_name=row.display_name,
        name=row.name,
        exercise=schemas.ExerciseRef(id=exercise.id, display_name=exercise.display_name),
        stage=stage_ref(exercise.stage, numbers),
        topics=[option_ref(t) for t in exercise.topics],
        source=option_ref(row.source),
        unit=row.unit,
        target=row.target,
        suggested_minutes=row.suggested_minutes,
        frequency=row.frequency,
        record_count=record_count,
        total_minutes=total_minutes,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[schemas.DrillSummary])
def list_drills(
    q: str | None = Query(
        default=None,
        description="Matches the drill's name or instructions, or a name or alias of its exercise",
    ),
    exercise_id: list[int] | None = Query(None),
    stage_id: list[int] | None = Query(None, description="The exercise's stage"),
    topic_id: list[int] | None = Query(None, description="One of the exercise's topics"),
    source_id: list[int] | None = Query(None),
    no_stage: bool = Query(False, description="Only the drills whose exercise has no stage"),
    db: Session = Depends(get_db),
):
    """A bare array in the roadmap order of their exercises - as
    `GET /api/exercises` - then by position inside each. A repeated parameter
    means "any of" its values."""
    numbers = stages.numbers(db)
    rows = drills.search(db, numbers, q, exercise_id, stage_id, topic_id, source_id, no_stage)
    totals = records.totals_by_drill(db, [row.id for row in rows])
    return [drill_summary(row, numbers, totals) for row in rows]


@router.get("/{drill_id}", response_model=schemas.DrillResponse)
def get_drill(drill_id: int, db: Session = Depends(get_db)):
    return drill_response(drills.get(db, drill_id))


@router.post("", response_model=schemas.DrillResponse, status_code=201)
def create_drill(payload: schemas.DrillCreate, db: Session = Depends(get_db)):
    return drill_response(drills.create(db, payload))


@router.patch("/{drill_id}", response_model=schemas.DrillResponse)
def update_drill(drill_id: int, payload: schemas.DrillUpdate, db: Session = Depends(get_db)):
    return drill_response(drills.update(db, drill_id, payload))


@router.delete("/{drill_id}", status_code=204)
def delete_drill(drill_id: int, db: Session = Depends(get_db)):
    """409 `{detail, records: n}` while records name the drill."""
    drills.delete(db, drill_id)
    return Response(status_code=204)
