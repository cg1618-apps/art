"""The one timer: starting it, its state machine, and saving it as a record.

**Every time is the database's.** A written timestamp is `now()`, and the
elapsed figure a pause or a stop folds in is computed against `SELECT now()`
read in the same transaction - which is the same value, since PostgreSQL's
`now()` is the transaction's start. The client's clock never reaches a row.

Each read hands back `(timer, now)` from one transaction, so the `now` a
response carries is the clock the row was read against. Each write locks the
row (`FOR UPDATE`), so two devices pressing pause at once are serialised
rather than both folding in the same running stretch.

Every refusal comes before anything is written, so a refused request changes
nothing - including saving it as a record, where a refused record write
leaves the timer as it was.
"""

import datetime as dt
import math

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.constants import TimerMode, TimerState
from app.errors import AppError
from app.models import ActiveTimer, Drill, Record
from app.services import records
from app.services.common import merged


def _query():
    return select(ActiveTimer).options(
        selectinload(ActiveTimer.drill).selectinload(Drill.exercise),
        selectinload(ActiveTimer.exercise),
    )


def _db_now(db: Session) -> dt.datetime:
    return db.execute(select(func.now())).scalar_one()


def current(db: Session) -> tuple[ActiveTimer | None, dt.datetime]:
    """The timer, or None, and the database clock - one transaction."""
    now = _db_now(db)
    return db.execute(_query()).scalar_one_or_none(), now


def _locked(db: Session) -> ActiveTimer:
    """The timer, locked for this transaction. 404 when there is none."""
    timer = db.execute(_query().with_for_update(of=ActiveTimer)).scalar_one_or_none()
    if timer is None:
        raise AppError(404, "There is no timer.")
    return timer


def _require(timer: ActiveTimer, *states: TimerState, action: str) -> None:
    if timer.state not in states:
        raise AppError(409, f"The timer is {timer.state}, so it cannot be {action}.")


def _check(db: Session, row: ActiveTimer | None, sent: dict, mode: TimerMode) -> None:
    """Every rule against the MERGED row, before anything is assigned."""
    target = merged(row, sent, "target_seconds")
    if mode == TimerMode.COUNTDOWN and target is None:
        raise AppError(422, "A countdown needs a target.")
    if mode == TimerMode.STOPWATCH and target is not None:
        raise AppError(422, "A stopwatch has no target.")
    records.refuse_both_activities(row, sent, "timer")
    records.check_exists(db, sent, records.ACTIVITY_ROWS)


def _fold_in_running(db: Session, timer: ActiveTimer) -> None:
    """Add the running stretch to `elapsed_seconds`, in whole seconds rounded
    down, and stop it running. The stretch is measured by the database's
    clock; a clock that stepped backwards adds nothing rather than going
    negative."""
    stretch = (_db_now(db) - timer.running_since).total_seconds()
    timer.elapsed_seconds += max(0, math.floor(stretch))
    timer.running_since = None


# --- writing ------------------------------------------------------------------


def start(db: Session, payload) -> None:
    """Running from now. 409 while any timer exists, whatever its state; the
    unique index is the backstop for two starts racing."""
    if db.execute(select(ActiveTimer.id)).first() is not None:
        raise AppError(409, "A timer already exists. Stop or discard it first.")
    sent = payload.model_dump()
    _check(db, None, sent, payload.mode)
    db.add(ActiveTimer(**sent, started_at=func.now(), running_since=func.now()))
    db.commit()


def update(db: Session, payload) -> None:
    """In any state, stopped included. A draft sent replaces the one held,
    whole; it is stored unchecked (see `RecordDraft`)."""
    timer = _locked(db)
    sent = {field: getattr(payload, field) for field in payload.model_fields_set}
    if sent.get("draft") is not None:
        sent["draft"] = sent["draft"].stored()
    _check(db, timer, sent, TimerMode(timer.mode))
    for field, value in sent.items():
        setattr(timer, field, value)
    db.commit()


def pause(db: Session) -> None:
    timer = _locked(db)
    _require(timer, TimerState.RUNNING, action="paused")
    _fold_in_running(db, timer)
    db.commit()


def resume(db: Session) -> None:
    timer = _locked(db)
    _require(timer, TimerState.PAUSED, action="resumed")
    timer.running_since = func.now()
    db.commit()


def stop(db: Session) -> None:
    """Running or paused -> stopped, with `elapsed_seconds` final. A stopped
    timer waits for its record, or for 捨棄."""
    timer = _locked(db)
    _require(timer, TimerState.RUNNING, TimerState.PAUSED, action="stopped")
    if timer.running_since is not None:
        _fold_in_running(db, timer)
    timer.stopped_at = func.now()
    db.commit()


def save_as_record(db: Session, payload) -> Record:
    """Create the record and delete the timer, in one transaction. Only a
    stopped timer; the record is checked exactly as `POST /api/records`
    checks it, and a refusal there leaves the timer untouched.

    The body is the record. The timer's draft is not merged into it - the
    form that sends the body opened with the draft already in it - and goes
    with the timer."""
    timer = _locked(db)
    if timer.state != TimerState.STOPPED:
        raise AppError(409, f"The timer is {timer.state}. Stop it before saving it as a record.")
    record = records.add(db, payload)
    db.delete(timer)
    db.commit()
    return records.get(db, record.id)


def discard(db: Session) -> None:
    """捨棄: the session is thrown away, in any state, its draft with it."""
    db.delete(_locked(db))
    db.commit()
