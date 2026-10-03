"""Reading and writing drills - the prescribed ways of practising an exercise.

Every refusal comes before anything is written, so a refused save changes
nothing.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.constants import SOURCE
from app.errors import AppError
from app.models import Drill, DrillResource, DrillSourceLink, Exercise, Record
from app.schemas.exercise import DRILL_LIST_FIELDS
from app.services import options, records, resources

#: The list fields, and the row each item becomes.
LINK_MODELS = {"source_links": DrillSourceLink, "resources": DrillResource}


def loaded_options():
    """What a drill response reads, for a drill reached through anything."""
    return (
        selectinload(Drill.exercise),
        selectinload(Drill.source),
        selectinload(Drill.source_links),
        selectinload(Drill.resources),
    )


def get(db: Session, drill_id: int) -> Drill:
    row = db.query(Drill).options(*loaded_options()).filter(Drill.id == drill_id).one_or_none()
    if row is None:
        raise AppError(404, "No such drill.")
    return row


def _check_exercise(db: Session, exercise_id: int) -> None:
    """An exercise_id naming no exercise is a malformed body, not a missing
    URL."""
    if db.get(Exercise, exercise_id) is None:
        raise AppError(422, f"No such exercise: {exercise_id}.")


def _last_position(db: Session, exercise_id: int) -> int:
    last = db.query(func.max(Drill.position)).filter(Drill.exercise_id == exercise_id).scalar()
    return 0 if last is None else last + 1


def _apply_lists(drill: Drill, lists: dict) -> None:
    for field, model in LINK_MODELS.items():
        if lists.get(field) is not None:
            # Replaced whole: the old rows are orphans and go in this flush.
            setattr(drill, field, resources.build(model, lists[field]))


def create(db: Session, payload) -> Drill:
    lists = {field: getattr(payload, field) for field in DRILL_LIST_FIELDS}
    scalars = payload.model_dump(exclude=set(DRILL_LIST_FIELDS))
    _check_exercise(db, scalars["exercise_id"])
    options.check_single(db, scalars, {"source_id": SOURCE})
    if scalars["position"] is None:
        scalars["position"] = _last_position(db, scalars["exercise_id"])

    drill = Drill(**scalars)
    _apply_lists(drill, lists)
    db.add(drill)
    db.commit()
    return get(db, drill.id)


def update(db: Session, drill_id: int, payload) -> Drill:
    drill = get(db, drill_id)
    sent = payload.model_fields_set
    lists = {field: getattr(payload, field) for field in DRILL_LIST_FIELDS if field in sent}
    scalars = {field: getattr(payload, field) for field in sent if field not in DRILL_LIST_FIELDS}

    options.check_single(db, scalars, {"source_id": SOURCE})
    if "exercise_id" in scalars and scalars["exercise_id"] != drill.exercise_id:
        _check_exercise(db, scalars["exercise_id"])
        if "position" not in scalars:
            scalars["position"] = _last_position(db, scalars["exercise_id"])

    for field, value in scalars.items():
        setattr(drill, field, value)
    _apply_lists(drill, lists)
    # A save that only touched the links writes no column of `drill`.
    drill.updated_at = func.now()
    db.commit()
    return get(db, drill_id)


def delete(db: Session, drill_id: int) -> None:
    """Refused while records name the drill; its links cascade."""
    drill = get(db, drill_id)
    records.refuse_if_named(db, "drill", Record.drill_id == drill.id)
    db.delete(drill)
    db.commit()
