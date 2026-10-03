"""The timer: the one running session, its state machine, and saving it as a
record.

Every answer carrying the timer carries `now`, the database's clock read in
the same transaction as the row. 404 when there is no timer, for everything
but GET (which answers `null`) and POST (which starts one).
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.routers.common import activity
from app.routers.records import record_response
from app.services import stages, timer

router = APIRouter(prefix="/api/timer", tags=["Timer"])


def _current(db: Session) -> schemas.TimerResponse | None:
    row, now = timer.current(db)
    if row is None:
        return None
    return schemas.TimerResponse(
        id=row.id,
        mode=row.mode,
        target_seconds=row.target_seconds,
        state=row.state,
        started_at=row.started_at,
        running_since=row.running_since,
        elapsed_seconds=row.elapsed_seconds,
        stopped_at=row.stopped_at,
        now=now,
        activity=activity(row),
        draft=row.draft,
    )


@router.get("", response_model=schemas.TimerResponse | None)
def get_timer(db: Session = Depends(get_db)):
    """The timer, or `null` when there is none - a 200 either way."""
    return _current(db)


@router.post("", response_model=schemas.TimerResponse, status_code=201)
def start_timer(payload: schemas.TimerCreate, db: Session = Depends(get_db)):
    """Running from now. 409 while one exists."""
    timer.start(db, payload)
    return _current(db)


@router.patch("", response_model=schemas.TimerResponse)
def update_timer(payload: schemas.TimerUpdate, db: Session = Depends(get_db)):
    """The target, the activity and the record draft, in any state. A `draft`
    sent replaces the whole draft; null clears it."""
    timer.update(db, payload)
    return _current(db)


@router.post("/pause", response_model=schemas.TimerResponse)
def pause_timer(db: Session = Depends(get_db)):
    """running -> paused; anything else 409."""
    timer.pause(db)
    return _current(db)


@router.post("/resume", response_model=schemas.TimerResponse)
def resume_timer(db: Session = Depends(get_db)):
    """paused -> running; anything else 409."""
    timer.resume(db)
    return _current(db)


@router.post("/stop", response_model=schemas.TimerResponse)
def stop_timer(db: Session = Depends(get_db)):
    """running or paused -> stopped, with the final `elapsed_seconds`."""
    timer.stop(db)
    return _current(db)


@router.post("/record", response_model=schemas.RecordResponse, status_code=201)
def save_timer_as_record(payload: schemas.RecordCreate, db: Session = Depends(get_db)):
    """The body is a record write, as `POST /api/records`. Creates the record
    and deletes the timer in one transaction; only for a stopped timer."""
    return record_response(timer.save_as_record(db, payload), stages.numbers(db))


@router.delete("", status_code=204)
def discard_timer(db: Session = Depends(get_db)):
    """捨棄: deletes it, in any state."""
    timer.discard(db)
    return Response(status_code=204)
