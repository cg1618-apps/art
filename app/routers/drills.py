"""Drills: one prescribed way of practising an exercise. Listed on their
exercise (`GET /api/exercises/{id}`), so there is no list here."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Drill
from app.routers.common import option_ref, resource_list
from app.services import drills

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
