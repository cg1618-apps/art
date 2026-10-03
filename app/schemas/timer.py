"""The timer on the wire.

Inputs are `extra="forbid"`; `TimerUpdate` is all-optional and applied with
`model_fields_set`. The target rule (a countdown has one, a stopwatch none)
and the one-activity rule are checked by the service against the merged row,
so a create and a PATCH go through the same check. Saving a stopped timer as
a record takes a `RecordCreate`, the body `POST /api/records` takes.

`RecordDraft` is the record a timer will become, filled in while it runs. Its
types are checked and nothing else: no id is looked up and no record rule is
applied, because a draft is half-typed by design. The record rules apply when
it is saved, to the body that saves it.
"""

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import RecordKind, TimerMode, TimerState
from app.schemas.common import not_null
from app.schemas.record import Activity


class DraftReference(BaseModel):
    """A reference row as typed: either half may still be blank, and the link
    is not checked until the record is saved."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    url: str | None = None


class RecordDraft(BaseModel):
    """A record write without its date, minutes and activity - those are the
    timer's. Every field may be left out: a key sent is a choice the owner
    made (null included - "no location" is a choice), a key left out was not
    touched. Stored with `exclude_unset`, so the difference survives."""

    model_config = ConfigDict(extra="forbid")

    kind: RecordKind | None = None
    stage_id: int | None = None
    goal_id: int | None = None
    method_id: int | None = None
    location_id: int | None = None
    tool_id: int | None = None
    references: list[DraftReference] | None = None
    notes: str | None = None

    @field_validator("kind", mode="before")
    @classmethod
    def kind_is_a_kind(cls, value):
        return not_null(value, "A record always has a kind; leave it out instead")

    @field_validator("references", mode="before")
    @classmethod
    def list_is_a_list(cls, value):
        return not_null(value, "Send [] for no references; null is not a list")

    def stored(self) -> dict[str, Any]:
        """What `active_timer.draft` holds: the keys sent, as JSON."""
        return self.model_dump(mode="json", exclude_unset=True)


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
    # Replaces the whole draft; null clears it.
    draft: RecordDraft | None = None


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
    # The record draft as stored - only the keys that were sent - or null.
    draft: dict[str, Any] | None = None
