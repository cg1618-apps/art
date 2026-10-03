"""System options on the wire.

Inputs are `extra="forbid"`, and `OptionUpdate` is all-optional and applied
with `model_fields_set`, as `food`'s updates are.
"""

from pydantic import BaseModel, ConfigDict, field_validator

from app.constants import OPTION_CATEGORIES
from app.schemas.common import normalise, not_null


def _value(value):
    """Trimmed, and never empty: `uq_system_option_value` compares trimmed
    values, so storing the untrimmed one would only hide the duplicate."""
    value = normalise(value)
    if value is None:
        raise ValueError("An option needs a value")
    return value


class OptionCategoryResponse(BaseModel):
    key: str
    label: str
    description: str


class OptionCreate(BaseModel):
    """`sort_order` left out puts the value last in its category."""

    model_config = ConfigDict(extra="forbid")

    category: str
    value: str
    description: str | None = None
    remark: str | None = None
    sort_order: int | None = None

    @field_validator("category")
    @classmethod
    def category_is_registered(cls, value: str) -> str:
        if value not in OPTION_CATEGORIES:
            raise ValueError(f"A category is one of {', '.join(OPTION_CATEGORIES)}")
        return value

    @field_validator("value", mode="before")
    @classmethod
    def value_is_trimmed(cls, value):
        return _value(value)

    @field_validator("description", "remark", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)


class OptionUpdate(BaseModel):
    """Only what was SENT is applied.

    `category` is declared so that sending it is refused with a sentence that
    says why, rather than a bare "extra inputs are not permitted": moving a
    value between categories would leave every link to it in the wrong field.
    """

    model_config = ConfigDict(extra="forbid")

    category: str | None = None
    value: str | None = None
    description: str | None = None
    remark: str | None = None
    sort_order: int | None = None

    @field_validator("category", mode="before")
    @classmethod
    def category_cannot_change(cls, value):
        raise ValueError(
            "An option's category cannot change; every link to it would be in the wrong field"
        )

    @field_validator("value", mode="before")
    @classmethod
    def value_is_trimmed(cls, value):
        return _value(value)

    @field_validator("description", "remark", mode="before")
    @classmethod
    def blank_is_absent(cls, value):
        return normalise(value)

    @field_validator("sort_order", mode="before")
    @classmethod
    def sort_order_not_null(cls, value):
        return not_null(value, "sort_order cannot be cleared")


class OptionResponse(BaseModel):
    id: int
    category: str
    value: str
    description: str | None = None
    remark: str | None = None
    sort_order: int
    # Every reference to this option: see `services.options.REFERENCES`.
    in_use: int = 0


class OptionRef(BaseModel):
    """How another row shows an option: its value, and its description for
    the tooltip."""

    id: int
    value: str
    description: str | None = None
