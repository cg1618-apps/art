"""Reading and writing notes. The router does HTTP; this does the work.

Writes validate everything before they change anything, so a refused save
changes nothing - `food`'s order.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.constants import NOTE_CATEGORY, TOPIC
from app.errors import AppError
from app.models import Note, NoteAlias, NoteResource, NoteTopic
from app.schemas.note import LIST_FIELDS, NAME_FIELDS, NEEDS_A_NAME
from app.services import options
from app.services.search import ESCAPE, contains


def _summary_loaded(query):
    return query.options(selectinload(Note.category), selectinload(Note.topics))


def _loaded(query):
    return _summary_loaded(query).options(
        selectinload(Note.aliases), selectinload(Note.resources)
    )


def get(db: Session, note_id: int) -> Note:
    row = _loaded(db.query(Note)).filter(Note.id == note_id).one_or_none()
    if row is None:
        raise AppError(404, "No such note.")
    return row


def matches(q: str):
    """Any name slot, an alias, or the summary. Not the body: a word inside a
    long note would bury the note you meant."""
    term = contains(q)
    alias_match = (
        select(NoteAlias.note_id)
        .where(func.lower(NoteAlias.value).like(func.lower(term), escape=ESCAPE))
        .scalar_subquery()
    )
    return or_(
        Note.name_cn.ilike(term, escape=ESCAPE),
        Note.name_en.ilike(term, escape=ESCAPE),
        Note.name_alt.ilike(term, escape=ESCAPE),
        Note.summary.ilike(term, escape=ESCAPE),
        Note.id.in_(alias_match),
    )


def search(
    db: Session,
    q: str | None = None,
    category_id: list[int] | None = None,
    topic_id: list[int] | None = None,
) -> list[Note]:
    """The library list, ordered by display name. Each repeated filter means
    "any of" its values; different filters narrow each other."""
    query = _summary_loaded(db.query(Note))
    if q and q.strip():
        query = query.filter(matches(q))
    if category_id:
        query = query.filter(Note.category_id.in_(category_id))
    if topic_id:
        query = query.filter(
            Note.id.in_(
                select(NoteTopic.note_id).where(NoteTopic.option_id.in_(topic_id)).scalar_subquery()
            )
        )
    rows = query.all()
    rows.sort(key=lambda r: (r.display_name.casefold(), r.id))
    return rows


# --- writing ------------------------------------------------------------------


def _check_refs(db: Session, scalars: dict, lists: dict) -> dict:
    """422 for any id naming a missing option or one of the wrong category.
    Returns the topic rows to assign, when topics were sent."""
    if scalars.get("category_id") is not None:
        options.fetch_in_category(db, [scalars["category_id"]], NOTE_CATEGORY)
    fetched = {}
    if lists.get("topic_ids") is not None:
        fetched["topics"] = options.fetch_in_category(db, lists["topic_ids"], TOPIC)
    return fetched


def _apply_aliases(note: Note, values: list[str]) -> None:
    """Reconciled by value: a kept alias keeps its row, so a save that changes
    nothing deletes and re-inserts nothing (and cannot trip uq_note_alias
    against the row it is replacing)."""
    wanted = list(dict.fromkeys(values))
    note.aliases = [row for row in note.aliases if row.value in wanted]
    kept = {row.value for row in note.aliases}
    note.aliases.extend(NoteAlias(value=v) for v in wanted if v not in kept)


def _resources(payload_resources) -> list[NoteResource]:
    return [
        NoteResource(position=position, name=resource.name, url=resource.url)
        for position, resource in enumerate(payload_resources)
    ]


def _apply_lists(note: Note, lists: dict, fetched: dict) -> None:
    if lists.get("aliases") is not None:
        _apply_aliases(note, lists["aliases"])
    if "topics" in fetched:
        note.topics = fetched["topics"]
    if lists.get("resources") is not None:
        # Replaced whole: the old rows are orphans and go in this flush.
        note.resources = _resources(lists["resources"])


def create(db: Session, payload) -> Note:
    lists = {field: getattr(payload, field) for field in LIST_FIELDS}
    scalars = payload.model_dump(exclude=set(LIST_FIELDS))
    fetched = _check_refs(db, scalars, lists)

    note = Note(**scalars)
    db.add(note)
    _apply_lists(note, lists, fetched)
    db.commit()
    return get(db, note.id)


def update(db: Session, note_id: int, payload) -> Note:
    note = get(db, note_id)
    sent = payload.model_fields_set
    lists = {field: getattr(payload, field) for field in LIST_FIELDS if field in sent}
    scalars = {field: getattr(payload, field) for field in sent if field not in LIST_FIELDS}

    # Against the MERGED row, before anything is assigned: assigning first
    # would let an autoflush write the nameless row.
    if not any(scalars.get(f, getattr(note, f)) for f in NAME_FIELDS):
        raise AppError(422, f"{NEEDS_A_NAME}.")
    fetched = _check_refs(db, scalars, lists)

    for field, value in scalars.items():
        setattr(note, field, value)
    _apply_lists(note, lists, fetched)
    # A save that only touched aliases, topics or resources writes no column
    # of `note`, so `onupdate` would not fire; the note was still edited.
    note.updated_at = func.now()
    db.commit()
    return get(db, note_id)


def delete(db: Session, note_id: int) -> None:
    db.delete(get(db, note_id))
    db.commit()
