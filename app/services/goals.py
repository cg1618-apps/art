"""Reading and writing goals - the levels of the roadmap.

Every refusal comes before anything is written, so a refused save changes
nothing.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.constants import GoalStatus
from app.errors import AppError
from app.models import Goal, Stage
from app.schemas.goal import GOAL_NEEDS_A_NAME
from app.services.common import check_dated_status, require_a_name

DUPLICATE_CODE = "Another goal already has that code."


def _loaded(query):
    return query.options(selectinload(Goal.stages))


def listed(db: Session) -> list[Goal]:
    """Every goal in roadmap order, each with its stages."""
    return _loaded(db.query(Goal)).order_by(Goal.position, Goal.id).all()


def get(db: Session, goal_id: int) -> Goal:
    row = _loaded(db.query(Goal)).filter(Goal.id == goal_id).one_or_none()
    if row is None:
        raise AppError(404, "No such goal.")
    return row


def _check_unique(db: Session, code: str, exclude_id: int | None = None) -> None:
    """Mirrors uq_goal_code. The schema has already trimmed `code`."""
    query = db.query(Goal.id).filter(Goal.code == code)
    if exclude_id is not None:
        query = query.filter(Goal.id != exclude_id)
    if query.first() is not None:
        raise AppError(409, DUPLICATE_CODE)


def _check_achieved_on(row: Goal | None, sent: dict) -> None:
    check_dated_status(row, sent, done=GoalStatus.ACHIEVED, date_field="achieved_on")


def create(db: Session, payload) -> Goal:
    scalars = payload.model_dump()
    _check_unique(db, scalars["code"])
    _check_achieved_on(None, scalars)
    if scalars["position"] is None:
        last = db.query(func.max(Goal.position)).scalar()
        scalars["position"] = 0 if last is None else last + 1

    goal = Goal(**scalars)
    db.add(goal)
    db.commit()
    return get(db, goal.id)


def update(db: Session, goal_id: int, payload) -> Goal:
    goal = get(db, goal_id)
    sent = {field: getattr(payload, field) for field in payload.model_fields_set}

    if "code" in sent:
        _check_unique(db, sent["code"], exclude_id=goal.id)
    require_a_name(goal, sent, GOAL_NEEDS_A_NAME)
    _check_achieved_on(goal, sent)

    for field, value in sent.items():
        setattr(goal, field, value)
    db.commit()
    return get(db, goal_id)


def delete(db: Session, goal_id: int) -> None:
    """Refused while the goal has stages: they are the roadmap, and losing
    them by deleting a level header would be the wrong surprise. Move or
    delete them first. `stage.goal_id`'s RESTRICT is the backstop."""
    goal = get(db, goal_id)
    count = db.query(func.count(Stage.id)).filter(Stage.goal_id == goal.id).scalar()
    if count:
        raise AppError(
            409,
            f"This goal still has {count} stage{'s' if count != 1 else ''}. "
            "Move or delete them first.",
            stages=count,
        )
    db.delete(goal)
    db.commit()
