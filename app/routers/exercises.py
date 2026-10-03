"""Exercises: the list in roadmap order, one exercise with its drills, and
the writes."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Exercise
from app.routers.common import option_ref, resource_list, stage_ref
from app.routers.drills import drill_response
from app.services import exercises, records, stages

router = APIRouter(prefix="/api/exercises", tags=["Exercises"])


def _counts(db: Session, ids: list[int]) -> tuple[dict, dict]:
    return exercises.drill_counts(db, ids), records.totals_by_exercise(db, ids)


def _summary_fields(row: Exercise, numbers: dict, drill_counts: dict, totals: dict) -> dict:
    record_count, total_minutes = totals.get(row.id, (0, 0))
    return {
        "id": row.id,
        "display_name": row.display_name,
        "name_cn": row.name_cn,
        "name_en": row.name_en,
        "name_alt": row.name_alt,
        "stage": stage_ref(row.stage, numbers),
        "topics": [option_ref(t) for t in row.topics],
        "description": row.description,
        "drill_count": drill_counts.get(row.id, 0),
        "record_count": record_count,
        "total_minutes": total_minutes,
        "updated_at": row.updated_at,
    }


def _response(db: Session, row: Exercise) -> schemas.ExerciseResponse:
    drill_counts, totals = _counts(db, [row.id])
    return schemas.ExerciseResponse(
        **_summary_fields(row, stages.numbers(db), drill_counts, totals),
        aliases=sorted(alias.value for alias in row.aliases),
        remark=row.remark,
        resources=resource_list(row.resources),
        drills=[drill_response(drill) for drill in row.drills],
        created_at=row.created_at,
    )


@router.get("", response_model=list[schemas.ExerciseSummary])
def list_exercises(
    q: str | None = Query(default=None, description="Matches a name, an alias or the description"),
    stage_id: list[int] | None = Query(None),
    topic_id: list[int] | None = Query(None),
    no_stage: bool = Query(False, description="Only the exercises with no stage"),
    db: Session = Depends(get_db),
):
    """A bare array in roadmap order: by stage number, the exercises with no
    stage last, then by display name. A repeated parameter means "any of"
    its values."""
    numbers = stages.numbers(db)
    rows = exercises.search(db, numbers, q, stage_id, topic_id, no_stage)
    drill_counts, totals = _counts(db, [row.id for row in rows])
    return [
        schemas.ExerciseSummary(**_summary_fields(row, numbers, drill_counts, totals))
        for row in rows
    ]


@router.get("/{exercise_id}", response_model=schemas.ExerciseResponse)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    return _response(db, exercises.get(db, exercise_id))


@router.post("", response_model=schemas.ExerciseResponse, status_code=201)
def create_exercise(payload: schemas.ExerciseCreate, db: Session = Depends(get_db)):
    return _response(db, exercises.create(db, payload))


@router.patch("/{exercise_id}", response_model=schemas.ExerciseResponse)
def update_exercise(
    exercise_id: int, payload: schemas.ExerciseUpdate, db: Session = Depends(get_db)
):
    return _response(db, exercises.update(db, exercise_id, payload))


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """409 `{detail, drills: n, records: m}` while the exercise has drills or
    records name it."""
    exercises.delete(db, exercise_id)
    return Response(status_code=204)
