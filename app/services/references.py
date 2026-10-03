"""Reading and writing references. The router does HTTP; this does the work.

Writes validate everything before they change anything, so a refused save
changes nothing - `food`'s order, as `notes` keeps it.
"""

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.constants import REFERENCE_GROUP
from app.errors import AppError
from app.models import Reference, ReferenceGroup
from app.schemas.reference import LIST_FIELDS
from app.services import options
from app.services.search import ESCAPE, contains, tagged_with

#: How long a library row's notes excerpt runs, in characters.
EXCERPT_LENGTH = 120


def _loaded(query):
    return query.options(selectinload(Reference.groups))


def get(db: Session, reference_id: int) -> Reference:
    row = _loaded(db.query(Reference)).filter(Reference.id == reference_id).one_or_none()
    if row is None:
        raise AppError(404, "No such reference.")
    return row


def matches(q: str):
    """The name, the link or the notes, case-insensitively."""
    term = contains(q)
    return or_(
        *(
            column.ilike(term, escape=ESCAPE)
            for column in (Reference.name, Reference.url, Reference.notes)
        )
    )


def search(
    db: Session,
    q: str | None = None,
    group_id: list[int] | None = None,
    no_group: bool = False,
) -> list[Reference]:
    """The library list, ordered by name, then id. A repeated `group_id`
    means "any of"; `no_group` keeps only the references in no group.
    Different filters narrow each other."""
    query = _loaded(db.query(Reference))
    if q and q.strip():
        query = query.filter(matches(q))
    if group_id:
        query = query.filter(
            tagged_with(Reference, ReferenceGroup.reference_id, ReferenceGroup.option_id, group_id)
        )
    if no_group:
        query = query.filter(~Reference.groups.any())
    rows = query.all()
    rows.sort(key=lambda r: (r.name.casefold(), r.id))
    return rows


def excerpt(notes: str | None, length: int = EXCERPT_LENGTH) -> str | None:
    """The start of `notes` as one line: whitespace collapsed, cut at
    `length` characters with an ellipsis. Markdown is left as typed."""
    if not notes:
        return None
    line = " ".join(notes.split())
    if len(line) <= length:
        return line
    return line[:length].rstrip() + "…"


# --- writing ------------------------------------------------------------------


def _fetch_groups(db: Session, lists: dict) -> dict:
    """422 for any id naming a missing option or one of the wrong category."""
    if lists.get("group_ids") is None:
        return {}
    return {"groups": options.fetch_in_category(db, lists["group_ids"], REFERENCE_GROUP)}


def create(db: Session, payload) -> Reference:
    lists = {field: getattr(payload, field) for field in LIST_FIELDS}
    scalars = payload.model_dump(exclude=set(LIST_FIELDS))
    fetched = _fetch_groups(db, lists)

    reference = Reference(**scalars)
    db.add(reference)
    reference.groups = fetched["groups"]
    db.commit()
    return get(db, reference.id)


def update(db: Session, reference_id: int, payload) -> Reference:
    reference = get(db, reference_id)
    sent = payload.model_fields_set
    lists = {field: getattr(payload, field) for field in LIST_FIELDS if field in sent}
    scalars = {field: getattr(payload, field) for field in sent if field not in LIST_FIELDS}
    fetched = _fetch_groups(db, lists)

    for field, value in scalars.items():
        setattr(reference, field, value)
    if "groups" in fetched:
        reference.groups = fetched["groups"]
    # A save that only moved groups writes no column of `reference`, so
    # `onupdate` would not fire; the reference was still edited.
    reference.updated_at = func.now()
    db.commit()
    return get(db, reference_id)


def delete(db: Session, reference_id: int) -> None:
    db.delete(get(db, reference_id))
    db.commit()
