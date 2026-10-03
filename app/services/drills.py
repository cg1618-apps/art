"""Reading and writing drills - the prescribed ways of practising an exercise.

Every refusal comes before anything is written, so a refused save changes
nothing.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.constants import SOURCE
from app.errors import AppError
from app.models import (
    Drill,
    DrillResource,
    DrillSourceLink,
    Exercise,
    ExerciseAlias,
    ExerciseTopic,
    Record,
)
from app.schemas.exercise import DRILL_LIST_FIELDS
from app.services import options, records, resources
from app.services.search import ESCAPE, contains, names_match, tagged_with

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


def matches(q: str):
    """The drill's own name or its instructions, or any name or alias of its
    exercise."""
    term = contains(q)
    exercise_match = (
        select(Exercise.id)
        .where(names_match(q, Exercise, ExerciseAlias.exercise_id, ExerciseAlias.value))
        .scalar_subquery()
    )
    return or_(
        Drill.name.ilike(term, escape=ESCAPE),
        Drill.instructions.ilike(term, escape=ESCAPE),
        Drill.exercise_id.in_(exercise_match),
    )


def search(
    db: Session,
    numbers: dict[int, int],
    q: str | None = None,
    exercise_id: list[int] | None = None,
    stage_id: list[int] | None = None,
    topic_id: list[int] | None = None,
    source_id: list[int] | None = None,
    no_stage: bool = False,
) -> list[Drill]:
    """In roadmap order of their exercise - as `exercises.search` orders
    exercises - then by position inside it. `numbers` is `stages.numbers`.
    Stage and topic are the exercise's: a drill has neither of its own. A
    repeated filter means "any of" its values; different filters narrow each
    other."""
    query = (
        db.query(Drill)
        .join(Drill.exercise)
        .options(
            selectinload(Drill.exercise).options(
                selectinload(Exercise.stage), selectinload(Exercise.topics)
            ),
            selectinload(Drill.source),
        )
    )
    if q and q.strip():
        query = query.filter(matches(q))
    if exercise_id:
        query = query.filter(Drill.exercise_id.in_(exercise_id))
    if stage_id:
        query = query.filter(Exercise.stage_id.in_(stage_id))
    if no_stage:
        query = query.filter(Exercise.stage_id.is_(None))
    if topic_id:
        query = query.filter(
            tagged_with(Exercise, ExerciseTopic.exercise_id, ExerciseTopic.option_id, topic_id)
        )
    if source_id:
        query = query.filter(Drill.source_id.in_(source_id))
    rows = query.all()
    unstaged = len(numbers)

    def roadmap_order(drill: Drill):
        exercise = drill.exercise
        stage = exercise.stage_id
        return (
            numbers.get(stage, unstaged) if stage is not None else unstaged,
            exercise.display_name.casefold(),
            exercise.id,
            drill.position,
            drill.id,
        )

    rows.sort(key=roadmap_order)
    return rows


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
