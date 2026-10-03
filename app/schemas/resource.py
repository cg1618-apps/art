"""A link kept beside a row - a note's resources, a stage's lectures.

`food`'s `tbd_link` on the wire. Every owner stores the list in its own
`<table>_resource` table, replaced whole on a save, so the order sent is the
order kept.
"""

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.common import normalise, normalise_link


class ResourceIn(BaseModel):
    """No position: a resource's order is its place in the list."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    url: str

    @field_validator("url", mode="before")
    @classmethod
    def url_is_a_web_address(cls, value):
        return normalise_link(value)

    @field_validator("name", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)


class ResourceResponse(BaseModel):
    id: int
    name: str | None = None
    url: str
