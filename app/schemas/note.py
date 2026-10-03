"""Notes on the wire.

Inputs are `extra="forbid"`. `NoteUpdate` is all-optional and applied with
`model_fields_set`: a list sent replaces the old one, `[]` clears it, and an
explicit `null` for a list is refused. The at-least-one-name rule is checked by
the service against the merged row on a PATCH, as `food`'s is.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.constants import Visibility
from app.schemas.common import clean_aliases, normalise, not_null, require_a_name
from app.schemas.option import OptionRef
from app.schemas.resource import ResourceIn, ResourceResponse

LIST_FIELDS = ("aliases", "topic_ids", "resources")
NEEDS_A_NAME = "A note needs at least one name"


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    aliases: list[str] = []
    category_id: int | None = None
    topic_ids: list[int] = []
    summary: str | None = None
    body: str | None = None
    remark: str | None = None
    visibility: Visibility = Visibility.PRIVATE
    resources: list[ResourceIn] = []

    @field_validator("name_cn", "name_en", "name_alt", "summary", "body", "remark", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator("aliases")
    @classmethod
    def aliases_are_clean(cls, values: list[str]) -> list[str]:
        return clean_aliases(values)

    @model_validator(mode="after")
    def at_least_one_name(self):
        # Mirrors ck_note_has_a_name.
        return require_a_name(self, NEEDS_A_NAME)


class NoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    aliases: list[str] | None = None
    category_id: int | None = None
    topic_ids: list[int] | None = None
    summary: str | None = None
    body: str | None = None
    remark: str | None = None
    visibility: Visibility | None = None
    resources: list[ResourceIn] | None = None

    @field_validator("name_cn", "name_en", "name_alt", "summary", "body", "remark", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    # Validators run only on fields that were sent, so an explicit null is
    # refused while an absent list is left alone.
    @field_validator(*LIST_FIELDS, mode="before")
    @classmethod
    def lists_are_lists(cls, value):
        return not_null(value, "Send [] to clear a list; null is not a list")

    @field_validator("visibility", mode="before")
    @classmethod
    def visibility_not_null(cls, value):
        return not_null(value, "Visibility cannot be cleared")

    @field_validator("aliases")
    @classmethod
    def aliases_are_clean(cls, values: list[str] | None) -> list[str] | None:
        return None if values is None else clean_aliases(values)


class NoteSummary(BaseModel):
    id: int
    display_name: str = ""
    name_cn: str | None = None
    name_en: str | None = None
    name_alt: str | None = None
    category: OptionRef | None = None
    topics: list[OptionRef] = []
    summary: str | None = None
    visibility: Visibility
    updated_at: datetime | None = None


class NoteResponse(NoteSummary):
    aliases: list[str] = []
    body: str | None = None
    remark: str | None = None
    resources: list[ResourceResponse] = []
    created_at: datetime | None = None
