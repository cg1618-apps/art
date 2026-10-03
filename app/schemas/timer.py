"""The timer on the wire.

Inputs are `extra="forbid"`; `TimerUpdate` is all-optional and applied with
`model_fields_set`. The target rule (a countdown has one, a stopwatch none)
and the one-activity rule are checked by the service against the merged row,
so a create and a PATCH go through the same check. Saving a stopped timer as
a record takes a `RecordCreate`, the body `POST /api/records` takes.
"""

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.constants import TimerMode, TimerState
from app.schemas.record import Activity


class TimerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: TimerMode
    # Mirrors ck_active_timer_target_positive.
    target_seconds: int | None = Field(default=None, ge=1)
    drill_id: int | None = None
    exercise_id: int | None = None


class TimerUpdate(BaseModel):
    """The mode is fixed once started; everything else here may change while
    the timer exists, stopped included."""

    model_config = ConfigDict(extra="forbid")

    target_seconds: int | None = Field(default=None, ge=1)
    drill_id: int | None = None
    exercise_id: int | None = None


class TimerResponse(BaseModel):
    """`now` is the database's clock at response time, read in the same
    transaction as the row: the browser offsets its own clock by it, so the
    live figure is `elapsed_seconds + (now - running_since)` whatever the
    laptop's clock says."""

    id: int
    mode: TimerMode
    target_seconds: int | None = None
    state: TimerState
    started_at: dt.datetime
    running_since: dt.datetime | None = None
    elapsed_seconds: int
    stopped_at: dt.datetime | None = None
    now: dt.datetime
    # Null when the timer names neither a drill nor an exercise.
    activity: Activity | None = None
