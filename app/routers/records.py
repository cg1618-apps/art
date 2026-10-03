"""Records: the log, one record, the writes, and the per-day summary."""

import datetime as dt

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app import schemas
from app.constants import RecordKind
from app.database import get_db
from app.models import Record
from app.routers.common import activity, goal_ref, option_ref, resource_list, stage_ref
from app.services import records, stages

router = APIRouter(prefix="/api/records", tags=["Records"])


def record_response(row: Record, numbers: dict[int, int]) -> schemas.RecordResponse:
    """`numbers` is `stages.numbers`. Public: saving the timer as a record
    answers with this too."""
    return schemas.RecordResponse(
        id=row.id,
        date=row.date,
        kind=row.kind,
        activity=activity(row),
        stage=stage_ref(row.stage, numbers),
        goal=goal_ref(row.goal),
        location=option_ref(row.location),
        duration_minutes=row.duration_minutes,
        method=option_ref(row.method),
        tool=option_ref(row.tool),
        references=resource_list(row.references),
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# Before /{record_id}, which would otherwise claim "summary" as an id.
@router.get("/summary", response_model=list[schemas.DaySummary])
def summarise_records(
    date_from: dt.date | None = Query(None, alias="from"),
    date_to: dt.date | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    """Per day with records, oldest first: `{date, minutes, records}`. Both
    ends are inclusive."""
    return [
        schemas.DaySummary(date=day, minutes=minutes, records=count)
        for day, minutes, count in records.summary(db, date_from, date_to)
    ]


@router.get("", response_model=list[schemas.RecordResponse])
def list_records(
    date_from: dt.date | None = Query(None, alias="from"),
    date_to: dt.date | None = Query(None, alias="to"),
    kind: RecordKind | None = Query(None),
    exercise_id: int | None = Query(
        None, description="Records naming it directly or through one of its drills"
    ),
    drill_id: int | None = Query(None),
    stage_id: int | None = Query(None),
    goal_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """A bare array, newest first. Both ends of the date range are
    inclusive."""
    rows = records.search(db, date_from, date_to, kind, exercise_id, drill_id, stage_id, goal_id)
    numbers = stages.numbers(db)
    return [record_response(row, numbers) for row in rows]


@router.get("/{record_id}", response_model=schemas.RecordResponse)
def get_record(record_id: int, db: Session = Depends(get_db)):
    return record_response(records.get(db, record_id), stages.numbers(db))


@router.post("", response_model=schemas.RecordResponse, status_code=201)
def create_record(payload: schemas.RecordCreate, db: Session = Depends(get_db)):
    return record_response(records.create(db, payload), stages.numbers(db))


@router.patch("/{record_id}", response_model=schemas.RecordResponse)
def update_record(record_id: int, payload: schemas.RecordUpdate, db: Session = Depends(get_db)):
    return record_response(records.update(db, record_id, payload), stages.numbers(db))


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, db: Session = Depends(get_db)):
    records.delete(db, record_id)
    return Response(status_code=204)
