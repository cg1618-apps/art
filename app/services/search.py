"""The one LIKE pattern every search box builds, as `food`'s, and the
name-and-alias match every named library shares.

A search term is text the user typed, not a pattern: `%`, `_` and the escape
character itself are matched literally.
"""

from sqlalchemy import func, or_, select

from app.schemas.common import NAME_FIELDS

ESCAPE = "\\"


def contains(q: str) -> str:
    """A LIKE pattern matching `q` anywhere, its wildcards escaped. Pass
    `escape=ESCAPE` to the `like` / `ilike` it is used in."""
    term = q.strip()
    for char in (ESCAPE, "%", "_"):
        term = term.replace(char, ESCAPE + char)
    return f"%{term}%"


def names_match(q: str, model, alias_owner_column, alias_value_column, *also):
    """`q` in any name slot of `model`, in one of its aliases, or in any of
    the `also` columns - case-insensitively."""
    term = contains(q)
    alias_match = (
        select(alias_owner_column)
        .where(func.lower(alias_value_column).like(func.lower(term), escape=ESCAPE))
        .scalar_subquery()
    )
    columns = [getattr(model, field) for field in NAME_FIELDS] + list(also)
    return or_(
        *(column.ilike(term, escape=ESCAPE) for column in columns),
        model.id.in_(alias_match),
    )


def tagged_with(model, link_owner_column, link_option_column, option_ids: list[int]):
    """`model` rows linked to ANY of `option_ids` through a `<table>_topic`
    table."""
    return model.id.in_(
        select(link_owner_column).where(link_option_column.in_(option_ids)).scalar_subquery()
    )
