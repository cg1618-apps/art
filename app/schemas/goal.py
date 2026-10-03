"""Goals and stages on the wire.

Inputs are `extra="forbid"`. The updates are all-optional and applied with
`model_fields_set`. The at-least-one-name rule and the date-iff-status rule
are checked by the service against the merged row, so a create and a PATCH go
through the same check.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.constants import GoalStatus, StageStatus
from app.schemas.common import normalise, not_null, require_a_name
from app.schemas.resource import ResourceIn, ResourceResponse

GOAL_NEEDS_A_NAME = "A goal needs at least one name"
STAGE_NEEDS_A_NAME = "A stage needs at least one name"
TEXT_FIELDS = ("name_cn", "name_en", "name_alt", "description", "test", "remark")


def _code(value):
    """Trimmed, and never empty: `uq_goal_code` compares what is stored."""
    value = normalise(value)
    if value is None:
        raise ValueError("A goal needs a code")
    return value


# --- goals ------------------------------------------------------------------


class GoalCreate(BaseModel):
    """`position` left out puts the goal last on the roadmap."""

    model_config = ConfigDict(extra="forbid")

    code: str
    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    position: int | None = None
    description: str | None = None
    test: str | None = None
    status: GoalStatus = GoalStatus.PLANNED
    achieved_on: date | None = None
    remark: str | None = None

    @field_validator("code", mode="before")
    @classmethod
    def code_is_trimmed(cls, value):
        return _code(value)

    @field_validator(*TEXT_FIELDS, mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @model_validator(mode="after")
    def at_least_one_name(self):
        # Mirrors ck_goal_has_a_name.
        return require_a_name(self, GOAL_NEEDS_A_NAME)


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = None
    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    position: int | None = None
    description: str | None = None
    test: str | None = None
    status: GoalStatus | None = None
    achieved_on: date | None = None
    remark: str | None = None

    @field_validator("code", mode="before")
    @classmethod
    def code_is_trimmed(cls, value):
        return _code(value)

    @field_validator(*TEXT_FIELDS, mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    # Validators run only on fields that were sent, so an explicit null is
    # refused while an absent one is left alone.
    @field_validator("position", "status", mode="before")
    @classmethod
    def cannot_be_cleared(cls, value):
        return not_null(value, "This field cannot be cleared")


# --- stages -----------------------------------------------------------------


class StageCreate(BaseModel):
    """`position` left out puts the stage last in its goal."""

    model_config = ConfigDict(extra="forbid")

    goal_id: int
    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    position: int | None = None
    description: str | None = None
    test: str | None = None
    status: StageStatus = StageStatus.NOT_STARTED
    passed_on: date | None = None
    remark: str | None = None
    resources: list[ResourceIn] = []

    @field_validator(*TEXT_FIELDS, mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @model_validator(mode="after")
    def at_least_one_name(self):
        # Mirrors ck_stage_has_a_name.
        return require_a_name(self, STAGE_NEEDS_A_NAME)


class StageUpdate(BaseModel):
    """A new `goal_id` moves the stage: last in that goal unless `position`
    is sent with it."""

    model_config = ConfigDict(extra="forbid")

    goal_id: int | None = None
    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    position: int | None = None
    description: str | None = None
    test: str | None = None
    status: StageStatus | None = None
    passed_on: date | None = None
    remark: str | None = None
    resources: list[ResourceIn] | None = None

    @field_validator(*TEXT_FIELDS, mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator("goal_id", "position", "status", mode="before")
    @classmethod
    def cannot_be_cleared(cls, value):
        return not_null(value, "This field cannot be cleared")

    @field_validator("resources", mode="before")
    @classmethod
    def list_is_a_list(cls, value):
        return not_null(value, "Send [] to clear a list; null is not a list")


# --- responses --------------------------------------------------------------


class GoalRef(BaseModel):
    """How a stage shows its goal."""

    id: int
    code: str
    display_name: str = ""


class StageSummary(BaseModel):
    id: int
    # Derived: every stage ordered by (goal position, stage position, id),
    # numbered from 0.
    number: int
    display_name: str = ""
    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    position: int
    description: str | None = None
    test: str | None = None
    status: StageStatus
    passed_on: date | None = None


class StageResponse(StageSummary):
    goal: GoalRef
    remark: str | None = None
    resources: list[ResourceResponse] = []


class GoalResponse(BaseModel):
    id: int
    code: str
    display_name: str = ""
    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    position: int
    description: str | None = None
    test: str | None = None
    status: GoalStatus
    achieved_on: date | None = None
    remark: str | None = None
    stages: list[StageSummary] = []
