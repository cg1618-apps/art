"""Reading and writing records, and the per-day summary.

Every refusal comes before anything is written, so a refused save changes
nothing. What a record names - drill, exercise, stage, goal - RESTRICTs that
row's delete; the services that delete those rows ask `count` first and
answer 409 with the number.
"""

import datetime as dt

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.constants import LOCATION, METHOD, TOOL, RecordKind
from app.errors import AppError
from app.models import Drill, Exercise, Goal, Record, RecordReference, Stage
from app.schemas.record import LIST_FIELDS
from app.services import options, resources
from app.services.common import merged

#: Each option a record names, and the category it must be.
OPTION_FIELDS = {"location_id": LOCATION, "method_id": METHOD, "tool_id": TOOL}

#: The activity a record - or the timer - names, and what a missing id is
#: called in the 422.
ACTIVITY_ROWS = {
    "drill_id": (Drill, "drill"),
    "exercise_id": (Exercise, "exercise"),
}

#: Each row a record names, and what a missing id is called in the 422.
NAMED_ROWS = {
    **ACTIVITY_ROWS,
    "stage_id": (Stage, "stage"),
    "goal_id": (Goal, "goal"),
}


def _loaded(query):
    return query.options(
        selectinload(Record.drill).selectinload(Drill.exercise),
        selectinload(Record.exercise),
        selectinload(Record.stage),
        selectinload(Record.goal),
        selectinload(Record.location),
        selectinload(Record.method),
        selectinload(Record.tool),
        selectinload(Record.references),
    )


def get(db: Session, record_id: int) -> Record:
    row = _loaded(db.query(Record)).filter(Record.id == record_id).one_or_none()
    if row is None:
        raise AppError(404, "No such record.")
    return row


# --- what names what ----------------------------------------------------------


def naming_exercise(exercise_ids):
    """Records naming any of `exercise_ids` directly, or through one of their
    drills. `exercise_ids` is one id or a list."""
    ids = exercise_ids if isinstance(exercise_ids, list) else [exercise_ids]
    through_drill = select(Drill.id).where(Drill.exercise_id.in_(ids)).scalar_subquery()
    return or_(Record.exercise_id.in_(ids), Record.drill_id.in_(through_drill))


def count(db: Session, *criteria) -> int:
    """How many records match `criteria` - the number a refused delete
    states."""
    return db.query(func.count(Record.id)).filter(*criteria).scalar()


def refuse_if_named(db: Session, what: str, *criteria) -> None:
    """409 `{detail, records}` while any record matches `criteria`. A record
    is history: deleting what it names is never a silent loss."""
    n = count(db, *criteria)
    if n:
        raise AppError(
            409,
            f"{n} record{'s' if n != 1 else ''} still name{'s' if n == 1 else ''} this {what}. "
            "Change or delete them first.",
            records=n,
        )


def totals_by_exercise(db: Session, exercise_ids: list[int]) -> dict[int, tuple[int, int]]:
    """Exercise id -> (records, minutes), counting records that name it
    directly or through a drill. A record with no duration adds no minutes."""
    exercise = func.coalesce(Record.exercise_id, Drill.exercise_id)
    query = (
        select(exercise, func.count(Record.id), func.coalesce(func.sum(Record.duration_minutes), 0))
        .select_from(Record)
        .outerjoin(Drill, Record.drill_id == Drill.id)
        .where(exercise.in_(exercise_ids))
        .group_by(exercise)
    )
    return {row[0]: (row[1], row[2]) for row in db.execute(query)}


def totals_by_drill(db: Session, drill_ids: list[int]) -> dict[int, tuple[int, int]]:
    """Drill id -> (records, minutes), counting records that name the drill.
    A record with no duration adds no minutes."""
    query = (
        select(
            Record.drill_id,
            func.count(Record.id),
            func.coalesce(func.sum(Record.duration_minutes), 0),
        )
        .where(Record.drill_id.in_(drill_ids))
        .group_by(Record.drill_id)
    )
    return {row[0]: (row[1], row[2]) for row in db.execute(query)}


# --- reading ------------------------------------------------------------------


def _in_range(query, date_from: dt.date | None, date_to: dt.date | None):
    if date_from is not None:
        query = query.filter(Record.date >= date_from)
    if date_to is not None:
        query = query.filter(Record.date <= date_to)
    return query


def search(
    db: Session,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    kind: RecordKind | None = None,
    exercise_id: int | None = None,
    drill_id: int | None = None,
    stage_id: int | None = None,
    goal_id: int | None = None,
) -> list[Record]:
    """Newest first: by date, then the later-written record first. Both ends
    of the date range are inclusive."""
    query = _in_range(_loaded(db.query(Record)), date_from, date_to)
    if kind is not None:
        query = query.filter(Record.kind == kind)
    if exercise_id is not None:
        query = query.filter(naming_exercise(exercise_id))
    if drill_id is not None:
        query = query.filter(Record.drill_id == drill_id)
    if stage_id is not None:
        query = query.filter(Record.stage_id == stage_id)
    if goal_id is not None:
        query = query.filter(Record.goal_id == goal_id)
    return query.order_by(Record.date.desc(), Record.id.desc()).all()


def summary(
    db: Session, date_from: dt.date | None = None, date_to: dt.date | None = None
) -> list[tuple[dt.date, int, int]]:
    """(date, minutes, records) per day with at least one record, oldest
    first. A record with no duration counts as a record and zero minutes."""
    query = db.query(
        Record.date,
        func.coalesce(func.sum(Record.duration_minutes), 0),
        func.count(Record.id),
    )
    query = _in_range(query, date_from, date_to).group_by(Record.date).order_by(Record.date)
    return [(day, minutes, records) for day, minutes, records in query.all()]


# --- writing ------------------------------------------------------------------


def refuse_both_activities(row, sent: dict, owner: str) -> None:
    """`ck_<table>_one_activity` against the MERGED row. `owner` is what the
    422 calls the row: "record", "timer"."""
    if merged(row, sent, "drill_id") is not None and merged(row, sent, "exercise_id") is not None:
        raise AppError(422, f"A {owner} names a drill or an exercise, not both.")


def check_exists(db: Session, sent: dict, named: dict) -> None:
    """422 for any id in `sent` naming a row that does not exist. `named` is
    `NAMED_ROWS`-shaped."""
    for field, (model, what) in named.items():
        if sent.get(field) is not None and db.get(model, sent[field]) is None:
            raise AppError(422, f"No such {what}: {sent[field]}.")


def _check(db: Session, row: Record | None, sent: dict) -> None:
    """Every rule against the MERGED row, before anything is assigned.
    Mutates `sent`: a kind set away from `test` clears the stage and goal
    unless the same save sends one."""
    refuse_both_activities(row, sent, "record")

    if "kind" in sent and sent["kind"] != RecordKind.TEST:
        for field in ("stage_id", "goal_id"):
            sent.setdefault(field, None)
    targets = sum(merged(row, sent, field) is not None for field in ("stage_id", "goal_id"))
    if merged(row, sent, "kind") == RecordKind.TEST:
        if targets != 1:
            raise AppError(422, "A test record names exactly one stage or one goal.")
    elif targets:
        raise AppError(422, "Only a test record names a stage or a goal.")

    check_exists(db, sent, NAMED_ROWS)
    options.check_single(db, sent, OPTION_FIELDS)


def add(db: Session, payload) -> Record:
    """Check and flush a new record WITHOUT committing, so a caller can make
    it part of a larger transaction - saving a stopped timer as a record
    deletes the timer in the same one. A refusal raises before anything is
    added."""
    scalars = payload.model_dump(exclude=set(LIST_FIELDS))
    _check(db, None, scalars)

    record = Record(**scalars)
    record.references = resources.build(RecordReference, payload.references)
    db.add(record)
    db.flush()
    return record


def create(db: Session, payload) -> Record:
    record = add(db, payload)
    db.commit()
    return get(db, record.id)


def update(db: Session, record_id: int, payload) -> Record:
    record = get(db, record_id)
    sent = {field: getattr(payload, field) for field in payload.model_fields_set}
    sent_references = sent.pop("references", None)
    _check(db, record, sent)

    for field, value in sent.items():
        setattr(record, field, value)
    if sent_references is not None:
        # Replaced whole: the old rows are orphans and go in this flush.
        record.references = resources.build(RecordReference, sent_references)
    # A save that only touched references writes no column of `record`.
    record.updated_at = func.now()
    db.commit()
    return get(db, record_id)


def delete(db: Session, record_id: int) -> None:
    """Its reference links cascade."""
    db.delete(get(db, record_id))
    db.commit()
