"""Reading and writing exercises - what is practised. The router does HTTP;
this does the work.

Writes validate everything before they change anything, so a refused save
changes nothing - `food`'s order, as `notes`.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.constants import TOPIC
from app.errors import AppError
from app.models import Drill, Exercise, ExerciseAlias, ExerciseResource, ExerciseTopic, Stage
from app.schemas.exercise import EXERCISE_LIST_FIELDS, EXERCISE_NEEDS_A_NAME
from app.services import drills, options, records, resources
from app.services.common import apply_aliases, require_a_name
from app.services.search import names_match, tagged_with


def _summary_loaded(query):
    return query.options(selectinload(Exercise.stage), selectinload(Exercise.topics))


def _loaded(query):
    return _summary_loaded(query).options(
        selectinload(Exercise.aliases),
        selectinload(Exercise.resources),
        selectinload(Exercise.drills).options(*drills.loaded_options()),
    )


def get(db: Session, exercise_id: int) -> Exercise:
    row = _loaded(db.query(Exercise)).filter(Exercise.id == exercise_id).one_or_none()
    if row is None:
        raise AppError(404, "No such exercise.")
    return row


def matches(q: str):
    """Any name slot, an alias, or the description."""
    return names_match(
        q, Exercise, ExerciseAlias.exercise_id, ExerciseAlias.value, Exercise.description
    )


def search(
    db: Session,
    numbers: dict[int, int],
    q: str | None = None,
    stage_id: list[int] | None = None,
    topic_id: list[int] | None = None,
    no_stage: bool = False,
) -> list[Exercise]:
    """In roadmap order - by stage number, the exercises with no stage last -
    then by display name. `numbers` is `stages.numbers`. A repeated filter
    means "any of" its values; different filters narrow each other."""
    query = _summary_loaded(db.query(Exercise))
    if q and q.strip():
        query = query.filter(matches(q))
    if stage_id:
        query = query.filter(Exercise.stage_id.in_(stage_id))
    if no_stage:
        query = query.filter(Exercise.stage_id.is_(None))
    if topic_id:
        query = query.filter(
            tagged_with(Exercise, ExerciseTopic.exercise_id, ExerciseTopic.option_id, topic_id)
        )
    rows = query.all()
    unstaged = len(numbers)
    rows.sort(
        key=lambda r: (
            numbers.get(r.stage_id, unstaged) if r.stage_id is not None else unstaged,
            r.display_name.casefold(),
            r.id,
        )
    )
    return rows


def drill_counts(db: Session, exercise_ids: list[int]) -> dict[int, int]:
    query = (
        select(Drill.exercise_id, func.count(Drill.id))
        .where(Drill.exercise_id.in_(exercise_ids))
        .group_by(Drill.exercise_id)
    )
    return dict(db.execute(query).all())


# --- writing ------------------------------------------------------------------


def _check_refs(db: Session, scalars: dict, lists: dict) -> dict:
    """422 for a stage that does not exist, or a topic id naming a missing
    option or one of the wrong category. Returns the topic rows to assign,
    when topics were sent."""
    stage_id = scalars.get("stage_id")
    if stage_id is not None and db.get(Stage, stage_id) is None:
        raise AppError(422, f"No such stage: {stage_id}.")
    fetched = {}
    if lists.get("topic_ids") is not None:
        fetched["topics"] = options.fetch_in_category(db, lists["topic_ids"], TOPIC)
    return fetched


def _apply_lists(exercise: Exercise, lists: dict, fetched: dict) -> None:
    if lists.get("aliases") is not None:
        apply_aliases(exercise, ExerciseAlias, lists["aliases"])
    if "topics" in fetched:
        exercise.topics = fetched["topics"]
    if lists.get("resources") is not None:
        # Replaced whole: the old rows are orphans and go in this flush.
        exercise.resources = resources.build(ExerciseResource, lists["resources"])


def create(db: Session, payload) -> Exercise:
    lists = {field: getattr(payload, field) for field in EXERCISE_LIST_FIELDS}
    scalars = payload.model_dump(exclude=set(EXERCISE_LIST_FIELDS))
    fetched = _check_refs(db, scalars, lists)

    exercise = Exercise(**scalars)
    db.add(exercise)
    _apply_lists(exercise, lists, fetched)
    db.commit()
    return get(db, exercise.id)


def update(db: Session, exercise_id: int, payload) -> Exercise:
    exercise = get(db, exercise_id)
    sent = payload.model_fields_set
    lists = {field: getattr(payload, field) for field in EXERCISE_LIST_FIELDS if field in sent}
    scalars = {
        field: getattr(payload, field) for field in sent if field not in EXERCISE_LIST_FIELDS
    }

    # Against the MERGED row, before anything is assigned: assigning first
    # would let an autoflush write the nameless row.
    require_a_name(exercise, scalars, EXERCISE_NEEDS_A_NAME)
    fetched = _check_refs(db, scalars, lists)

    for field, value in scalars.items():
        setattr(exercise, field, value)
    _apply_lists(exercise, lists, fetched)
    # A save that only touched aliases, topics or resources writes no column
    # of `exercise`, so `onupdate` would not fire; it was still edited.
    exercise.updated_at = func.now()
    db.commit()
    return get(db, exercise_id)


def delete(db: Session, exercise_id: int) -> None:
    """Refused while the exercise has drills, or records name it directly or
    through a drill: 409 `{detail, drills, records}`. Its aliases, resources
    and topic links cascade."""
    exercise = get(db, exercise_id)
    drill_count = len(exercise.drills)
    record_count = records.count(db, records.naming_exercise(exercise.id))
    if drill_count or record_count:
        parts = []
        if drill_count:
            parts.append(f"{drill_count} drill{'s' if drill_count != 1 else ''}")
        if record_count:
            parts.append(f"{record_count} record{'s' if record_count != 1 else ''}")
        raise AppError(
            409,
            f"This exercise still has {' and '.join(parts)}. Move or delete them first.",
            drills=drill_count,
            records=record_count,
        )
    db.delete(exercise)
    db.commit()
