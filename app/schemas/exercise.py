"""Exercises and drills on the wire.

Inputs are `extra="forbid"`. Updates are all-optional and applied with
`model_fields_set`: a list sent replaces the old one, `[]` clears it, and an
explicit `null` for a list is refused - `note`'s rules. The at-least-one-name
rule is checked by the service against the merged row on a PATCH.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import clean_aliases, normalise, not_null, require_a_name
from app.schemas.goal import StageRef
from app.schemas.option import OptionRef
from app.schemas.resource import ResourceIn, ResourceResponse

EXERCISE_LIST_FIELDS = ("aliases", "topic_ids", "resources")
EXERCISE_TEXT_FIELDS = ("name_cn", "name_en", "name_alt", "description", "remark")
EXERCISE_NEEDS_A_NAME = "An exercise needs at least one name"

DRILL_LIST_FIELDS = ("source_links", "resources")
DRILL_TEXT_FIELDS = ("name", "instructions", "unit", "frequency", "remark")

NULL_LIST = "Send [] to clear a list; null is not a list"


# --- exercises ----------------------------------------------------------------


class ExerciseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    aliases: list[str] = []
    stage_id: int | None = None
    topic_ids: list[int] = []
    description: str | None = None
    remark: str | None = None
    resources: list[ResourceIn] = []

    @field_validator(*EXERCISE_TEXT_FIELDS, mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator("aliases")
    @classmethod
    def aliases_are_clean(cls, values: list[str]) -> list[str]:
        return clean_aliases(values)

    @model_validator(mode="after")
    def at_least_one_name(self):
        # Mirrors ck_exercise_has_a_name.
        return require_a_name(self, EXERCISE_NEEDS_A_NAME)


class ExerciseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    aliases: list[str] | None = None
    stage_id: int | None = None
    topic_ids: list[int] | None = None
    description: str | None = None
    remark: str | None = None
    resources: list[ResourceIn] | None = None

    @field_validator(*EXERCISE_TEXT_FIELDS, mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator(*EXERCISE_LIST_FIELDS, mode="before")
    @classmethod
    def lists_are_lists(cls, value):
        return not_null(value, NULL_LIST)

    @field_validator("aliases")
    @classmethod
    def aliases_are_clean(cls, values: list[str] | None) -> list[str] | None:
        return None if values is None else clean_aliases(values)


# --- drills -------------------------------------------------------------------


class DrillCreate(BaseModel):
    """`position` left out puts the drill last in its exercise."""

    model_config = ConfigDict(extra="forbid")

    exercise_id: int
    name: str | None = None
    source_id: int | None = None
    source_links: list[ResourceIn] = []
    resources: list[ResourceIn] = []
    instructions: str | None = None
    unit: str | None = None
    # Mirror ck_drill_target_positive and ck_drill_suggested_minutes_positive.
    target: int | None = Field(default=None, ge=1)
    suggested_minutes: int | None = Field(default=None, ge=1)
    frequency: str | None = None
    remark: str | None = None
    position: int | None = None

    @field_validator(*DRILL_TEXT_FIELDS, mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)


class DrillUpdate(BaseModel):
    """A new `exercise_id` moves the drill: last in that exercise unless
    `position` is sent with it."""

    model_config = ConfigDict(extra="forbid")

    exercise_id: int | None = None
    name: str | None = None
    source_id: int | None = None
    source_links: list[ResourceIn] | None = None
    resources: list[ResourceIn] | None = None
    instructions: str | None = None
    unit: str | None = None
    target: int | None = Field(default=None, ge=1)
    suggested_minutes: int | None = Field(default=None, ge=1)
    frequency: str | None = None
    remark: str | None = None
    position: int | None = None

    @field_validator(*DRILL_TEXT_FIELDS, mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator("exercise_id", "position", mode="before")
    @classmethod
    def cannot_be_cleared(cls, value):
        return not_null(value, "This field cannot be cleared")

    @field_validator(*DRILL_LIST_FIELDS, mode="before")
    @classmethod
    def lists_are_lists(cls, value):
        return not_null(value, NULL_LIST)


# --- responses ----------------------------------------------------------------


class ExerciseRef(BaseModel):
    id: int
    display_name: str = ""


class DrillRef(BaseModel):
    id: int
    # The drill's own name, or its exercise's.
    display_name: str = ""


class DrillResponse(BaseModel):
    id: int
    exercise: ExerciseRef
    display_name: str = ""
    name: str | None = None
    source: OptionRef | None = None
    source_links: list[ResourceResponse] = []
    resources: list[ResourceResponse] = []
    instructions: str | None = None
    unit: str | None = None
    target: int | None = None
    suggested_minutes: int | None = None
    frequency: str | None = None
    remark: str | None = None
    position: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DrillSummary(BaseModel):
    """A row of the drill list: the drill, with its exercise's stage and
    topics so the list can group and filter without a second read."""

    id: int
    display_name: str = ""
    name: str | None = None
    exercise: ExerciseRef
    # The exercise's stage and topics; a drill has neither of its own.
    stage: StageRef | None = None
    topics: list[OptionRef] = []
    source: OptionRef | None = None
    unit: str | None = None
    target: int | None = None
    suggested_minutes: int | None = None
    frequency: str | None = None
    # Records naming this drill.
    record_count: int = 0
    # Their durations summed; a record with none counts as zero.
    total_minutes: int = 0
    updated_at: datetime | None = None


class ExerciseSummary(BaseModel):
    id: int
    display_name: str = ""
    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    stage: StageRef | None = None
    topics: list[OptionRef] = []
    description: str | None = None
    drill_count: int = 0
    # Records naming the exercise directly or through one of its drills.
    record_count: int = 0
    # Their durations summed; a record with none counts as zero.
    total_minutes: int = 0
    updated_at: datetime | None = None


class ExerciseResponse(ExerciseSummary):
    aliases: list[str] = []
    remark: str | None = None
    resources: list[ResourceResponse] = []
    drills: list[DrillResponse] = []
    created_at: datetime | None = None
