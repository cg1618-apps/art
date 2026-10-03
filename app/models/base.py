"""Shared pieces the model modules build on.

`in_clause` and `TimestampMixin` are `travel`'s; `NameFallbackMixin` is
`food`'s. art's skeleton is `travel`'s and its named rows are `food`'s shape,
so each is copied from the app it was proven in.
"""

from collections.abc import Iterable

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


def in_clause(column: str, vocabulary: Iterable[str], *, nullable: bool = False) -> str:
    """The SQL for a CheckConstraint restricting `column` to `vocabulary`.

    Built from the vocabulary rather than written out, so adding a member
    cannot leave the constraint behind - a drift that shows up as an insert
    failing on a value the application believes is legal.

    `vocabulary` is any iterable of strings: a `StrEnum` (its members are
    their values) or the keys of a registry such as `OPTION_CATEGORIES`.
    `travel`'s takes an enum only; art also builds one from a dict.

    `nullable` matters: `col IN (...)` is NULL, not TRUE, for a NULL column,
    and a CheckConstraint passes on NULL - but saying so explicitly documents
    that the column is allowed to be empty.
    """
    values = ", ".join(f"'{str(member)}'" for member in vocabulary)
    clause = f"{column} IN ({values})"
    return f"{column} IS NULL OR {clause}" if nullable else clause


class TimestampMixin:
    """`created_at` and `updated_at`, defaulted by the database.

    From the database clock rather than a Python helper, so a row written by a
    migration or by hand is stamped the same way as one written by the app.
    """

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class NameFallbackMixin:
    """`display_name` and `all_names` for a row with the name slots.

    `name_cn` leads, as in `food`: one user reading Chinese first.
    """

    @property
    def display_name(self) -> str:
        """The first name slot that holds something: cn, en, alt.

        "" rather than None when every slot is empty, so a caller can sort
        without a null check. The database forbids that state
        (`ck_<table>_has_a_name`), but this also runs on unflushed rows.
        """
        for value in (self.name_cn, self.name_en, getattr(self, "name_alt", None)):
            if value and value.strip():
                return value
        return ""

    def all_names(self) -> list[str]:
        """Every non-empty name slot. Aliases are not included: they live in
        their own table and a caller that wants them joins."""
        slots = (self.name_cn, self.name_en, getattr(self, "name_alt", None))
        return [v for v in slots if v and v.strip()]
