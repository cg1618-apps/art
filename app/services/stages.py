"""Reading and writing stages, and the number every stage is shown with.

Every refusal comes before anything is written, so a refused save changes
nothing.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.constants import StageStatus
from app.errors import AppError
from app.models import Goal, Stage, StageResource
from app.schemas.goal import STAGE_NEEDS_A_NAME
from app.services import resources
from app.services.common import check_dated_status, require_a_name


def numbers(db: Session) -> dict[int, int]:
    """Stage id -> its number: every stage ordered by (goal position, stage
    position, id), numbered from 0. Derived on every read, never stored, so a
    move renumbers everything after it for free."""
    query = (
        select(Stage.id)
        .join(Goal, Stage.goal_id == Goal.id)
        .order_by(Goal.position, Goal.id, Stage.position, Stage.id)
    )
    return {stage_id: number for number, stage_id in enumerate(db.scalars(query))}


def get(db: Session, stage_id: int) -> Stage:
    row = (
        db.query(Stage)
        .options(selectinload(Stage.goal), selectinload(Stage.resources))
        .filter(Stage.id == stage_id)
        .one_or_none()
    )
    if row is None:
        raise AppError(404, "No such stage.")
    return row


def _check_goal(db: Session, goal_id: int) -> None:
    """A goal_id naming no goal is a malformed body, not a missing URL."""
    if db.get(Goal, goal_id) is None:
        raise AppError(422, f"No such goal: {goal_id}.")


def _last_position(db: Session, goal_id: int) -> int:
    last = db.query(func.max(Stage.position)).filter(Stage.goal_id == goal_id).scalar()
    return 0 if last is None else last + 1


def _check_passed_on(row: Stage | None, sent: dict) -> None:
    check_dated_status(row, sent, done=StageStatus.PASSED, date_field="passed_on")


def create(db: Session, payload) -> Stage:
    scalars = payload.model_dump(exclude={"resources"})
    _check_goal(db, scalars["goal_id"])
    _check_passed_on(None, scalars)
    if scalars["position"] is None:
        scalars["position"] = _last_position(db, scalars["goal_id"])

    stage = Stage(**scalars)
    stage.resources = resources.build(StageResource, payload.resources)
    db.add(stage)
    db.commit()
    return get(db, stage.id)


def update(db: Session, stage_id: int, payload) -> Stage:
    stage = get(db, stage_id)
    sent = {field: getattr(payload, field) for field in payload.model_fields_set}
    sent_resources = sent.pop("resources", None)

    # Against the MERGED row, before anything is assigned: assigning first
    # would let an autoflush write a row the constraints refuse.
    require_a_name(stage, sent, STAGE_NEEDS_A_NAME)
    _check_passed_on(stage, sent)
    if "goal_id" in sent and sent["goal_id"] != stage.goal_id:
        _check_goal(db, sent["goal_id"])
        if "position" not in sent:
            sent["position"] = _last_position(db, sent["goal_id"])

    for field, value in sent.items():
        setattr(stage, field, value)
    if sent_resources is not None:
        # Replaced whole: the old rows are orphans and go in this flush.
        stage.resources = resources.build(StageResource, sent_resources)
    # A save that only touched resources writes no column of `stage`, so
    # `onupdate` would not fire; the stage was still edited.
    stage.updated_at = func.now()
    db.commit()
    return get(db, stage_id)


def delete(db: Session, stage_id: int) -> None:
    """Its resources cascade."""
    db.delete(get(db, stage_id))
    db.commit()
