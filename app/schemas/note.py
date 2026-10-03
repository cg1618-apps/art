"""Notes on the wire.

Inputs are `extra="forbid"`. `NoteUpdate` is all-optional and applied with
`model_fields_set`: a list sent replaces the old one, `[]` clears it, and an
explicit `null` for a list - or for the name - is refused.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.constants import Visibility
from app.schemas.common import normalise, not_null, required_text
from app.schemas.option import OptionRef
from app.schemas.resource import ResourceIn, ResourceResponse

LIST_FIELDS = ("topic_ids", "resources")
NEEDS_A_NAME = "A note needs a name"


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category_id: int | None = None
    topic_ids: list[int] = []
    summary: str | None = None
    body: str | None = None
    remark: str | None = None
    visibility: Visibility = Visibility.PRIVATE
    resources: list[ResourceIn] = []

    @field_validator("name", mode="before")
    @classmethod
    def name_is_not_blank(cls, value):
        # Mirrors ck_note_name_not_blank.
        return required_text(value, NEEDS_A_NAME)

    @field_validator("summary", "body", "remark", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)


class NoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    category_id: int | None = None
    topic_ids: list[int] | None = None
    summary: str | None = None
    body: str | None = None
    remark: str | None = None
    visibility: Visibility | None = None
    resources: list[ResourceIn] | None = None

    # Validators run only on fields that were sent, so a name or a list left
    # out is left alone while an explicit null (or a blank name) is refused.
    @field_validator("name", mode="before")
    @classmethod
    def name_is_not_blank(cls, value):
        return required_text(value, NEEDS_A_NAME)

    @field_validator("summary", "body", "remark", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator(*LIST_FIELDS, mode="before")
    @classmethod
    def lists_are_lists(cls, value):
        return not_null(value, "Send [] to clear a list; null is not a list")

    @field_validator("visibility", mode="before")
    @classmethod
    def visibility_not_null(cls, value):
        return not_null(value, "Visibility cannot be cleared")


class NoteSummary(BaseModel):
    id: int
    name: str
    category: OptionRef | None = None
    topics: list[OptionRef] = []
    summary: str | None = None
    visibility: Visibility
    updated_at: datetime | None = None


class NoteResponse(NoteSummary):
    body: str | None = None
    remark: str | None = None
    resources: list[ResourceResponse] = []
    created_at: datetime | None = None
