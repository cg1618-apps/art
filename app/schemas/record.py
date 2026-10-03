"""Records on the wire.

Inputs are `extra="forbid"`; `RecordUpdate` is all-optional and applied with
`model_fields_set`. The one-activity rule and the test-target rule are checked
by the service against the merged row, so a create and a PATCH go through the
same check.
"""

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import RecordKind
from app.schemas.common import normalise, not_null
from app.schemas.exercise import DrillRef, ExerciseRef
from app.schemas.goal import GoalRef, StageRef
from app.schemas.option import OptionRef
from app.schemas.resource import ResourceIn, ResourceResponse

LIST_FIELDS = ("references",)


class RecordCreate(BaseModel):
    """Names a drill, an exercise, or neither. A `test` names exactly one of
    stage and goal; any other kind names neither."""

    model_config = ConfigDict(extra="forbid")

    date: dt.date
    location_id: int | None = None
    # Mirrors ck_record_duration_non_negative.
    duration_minutes: int | None = Field(default=None, ge=0)
    drill_id: int | None = None
    exercise_id: int | None = None
    kind: RecordKind = RecordKind.PRACTICE
    stage_id: int | None = None
    goal_id: int | None = None
    method_id: int | None = None
    tool_id: int | None = None
    references: list[ResourceIn] = []
    notes: str | None = None

    @field_validator("notes", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)


class RecordUpdate(BaseModel):
    """Setting `kind` away from `test` clears the stage and goal, unless the
    same save sends one - which is then a 422, not a silent drop."""

    model_config = ConfigDict(extra="forbid")

    date: dt.date | None = None
    location_id: int | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    drill_id: int | None = None
    exercise_id: int | None = None
    kind: RecordKind | None = None
    stage_id: int | None = None
    goal_id: int | None = None
    method_id: int | None = None
    tool_id: int | None = None
    references: list[ResourceIn] | None = None
    notes: str | None = None

    @field_validator("notes", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator("date", "kind", mode="before")
    @classmethod
    def cannot_be_cleared(cls, value):
        return not_null(value, "This field cannot be cleared")

    @field_validator("references", mode="before")
    @classmethod
    def list_is_a_list(cls, value):
        return not_null(value, "Send [] to clear a list; null is not a list")


class Activity(BaseModel):
    """What was practised. `drill` is null when the record names the exercise
    directly; through a drill, `exercise` is the drill's."""

    exercise: ExerciseRef
    drill: DrillRef | None = None


class RecordResponse(BaseModel):
    id: int
    date: dt.date
    kind: RecordKind
    # Null when the record names neither a drill nor an exercise.
    activity: Activity | None = None
    # Only on a test, and exactly one of the two.
    stage: StageRef | None = None
    goal: GoalRef | None = None
    location: OptionRef | None = None
    duration_minutes: int | None = None
    method: OptionRef | None = None
    tool: OptionRef | None = None
    references: list[ResourceResponse] = []
    notes: str | None = None
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None


class DaySummary(BaseModel):
    """One day with records: its minutes summed (a record with no duration
    adds none) and how many records."""

    date: dt.date
    minutes: int
    records: int
