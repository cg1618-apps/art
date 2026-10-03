"""Reading and writing notes. The router does HTTP; this does the work.

Writes validate everything before they change anything, so a refused save
changes nothing - `food`'s order.
"""

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.constants import NOTE_CATEGORY, TOPIC
from app.errors import AppError
from app.models import Note, NoteResource, NoteTopic
from app.schemas.note import LIST_FIELDS
from app.services import options, resources
from app.services.search import ESCAPE, contains, tagged_with


def _summary_loaded(query):
    return query.options(selectinload(Note.category), selectinload(Note.topics))


def _loaded(query):
    return _summary_loaded(query).options(selectinload(Note.resources))


def get(db: Session, note_id: int) -> Note:
    row = _loaded(db.query(Note)).filter(Note.id == note_id).one_or_none()
    if row is None:
        raise AppError(404, "No such note.")
    return row


def matches(q: str):
    """The name, the summary or the body, case-insensitively."""
    term = contains(q)
    return or_(*(column.ilike(term, escape=ESCAPE) for column in (Note.name, Note.summary, Note.body)))


def search(
    db: Session,
    q: str | None = None,
    category_id: list[int] | None = None,
    topic_id: list[int] | None = None,
) -> list[Note]:
    """The library list, ordered by name. Each repeated filter means "any of"
    its values; different filters narrow each other."""
    query = _summary_loaded(db.query(Note))
    if q and q.strip():
        query = query.filter(matches(q))
    if category_id:
        query = query.filter(Note.category_id.in_(category_id))
    if topic_id:
        query = query.filter(tagged_with(Note, NoteTopic.note_id, NoteTopic.option_id, topic_id))
    rows = query.all()
    rows.sort(key=lambda r: (r.name.casefold(), r.id))
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


def _apply_lists(note: Note, lists: dict, fetched: dict) -> None:
    if "topics" in fetched:
        note.topics = fetched["topics"]
    if lists.get("resources") is not None:
        # Replaced whole: the old rows are orphans and go in this flush.
        note.resources = resources.build(NoteResource, lists["resources"])


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
    fetched = _check_refs(db, scalars, lists)

    for field, value in scalars.items():
        setattr(note, field, value)
    _apply_lists(note, lists, fetched)
    # A save that only touched topics or resources writes no column of
    # `note`, so `onupdate` would not fire; the note was still edited.
    note.updated_at = func.now()
    db.commit()
    return get(db, note_id)


def delete(db: Session, note_id: int) -> None:
    db.delete(get(db, note_id))
    db.commit()
