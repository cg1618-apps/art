"""References on the wire.

Inputs are `extra="forbid"`. `ReferenceUpdate` is all-optional and applied
with `model_fields_set`: `group_ids` sent replaces the old list, `[]` clears
it, and an explicit `null` for it - or for the name or the link - is refused.
The link is a resource's: http or https, and `https://` added when no scheme
was typed.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.common import normalise, normalise_link, not_null, required_text
from app.schemas.option import OptionRef

LIST_FIELDS = ("group_ids",)
NEEDS_A_NAME = "A reference needs a name"


class ReferenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    url: str
    group_ids: list[int] = []
    notes: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def name_is_not_blank(cls, value):
        # Mirrors ck_reference_name_not_blank.
        return required_text(value, NEEDS_A_NAME)

    @field_validator("url", mode="before")
    @classmethod
    def url_is_a_web_address(cls, value):
        return normalise_link(value)

    @field_validator("notes", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)


class ReferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    url: str | None = None
    group_ids: list[int] | None = None
    notes: str | None = None

    # Validators run only on fields that were sent, so a field left out is
    # left alone while an explicit null is refused.
    @field_validator("name", mode="before")
    @classmethod
    def name_is_not_blank(cls, value):
        return required_text(value, NEEDS_A_NAME)

    @field_validator("url", mode="before")
    @classmethod
    def url_is_a_web_address(cls, value):
        return normalise_link(not_null(value, "A reference needs a URL"))

    @field_validator("notes", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator(*LIST_FIELDS, mode="before")
    @classmethod
    def lists_are_lists(cls, value):
        return not_null(value, "Send [] to clear a list; null is not a list")


class ReferenceSummary(BaseModel):
    """A library row. `notes_excerpt` is the start of the notes as one line;
    the notes themselves are on the detail, as a note's body is."""

    id: int
    name: str
    url: str
    groups: list[OptionRef] = []
    notes_excerpt: str | None = None
    updated_at: datetime | None = None


class ReferenceResponse(BaseModel):
    id: int
    name: str
    url: str
    groups: list[OptionRef] = []
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
