"""Reading and writing system options, and resolving the ids other rows name.

Every refusal comes before anything is written, so a refused save changes
nothing.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import OPTION_CATEGORIES
from app.errors import AppError, StaleCountError
from app.models import Note, NoteTopic, SystemOption

DUPLICATE = "That category already has that value."


def _category_position(category: str) -> int:
    return list(OPTION_CATEGORIES).index(category)


def in_use_counts(db: Session, ids: list[int] | None = None) -> dict[int, int]:
    """Per option: notes whose category is it, plus topic links naming it.

    Two grouped queries rather than a join, so a note carrying an option both
    as its category and as a topic counts twice - which is right, since the
    delete removes both references.
    """
    counts: dict[int, int] = {}
    queries = (
        select(Note.category_id, func.count()).where(Note.category_id.is_not(None)).group_by(
            Note.category_id
        ),
        select(NoteTopic.option_id, func.count()).group_by(NoteTopic.option_id),
    )
    for query in queries:
        column = query.selected_columns[0]
        if ids is not None:
            query = query.where(column.in_(ids))
        for option_id, count in db.execute(query):
            counts[option_id] = counts.get(option_id, 0) + count
    return counts


def in_use(db: Session, option_id: int) -> int:
    return in_use_counts(db, [option_id]).get(option_id, 0)


def check_category(category: str) -> None:
    if category not in OPTION_CATEGORIES:
        raise AppError(
            422, f"No such category: {category}. One of {', '.join(OPTION_CATEGORIES)}."
        )


def listed(db: Session, category: str | None = None) -> list[SystemOption]:
    """In the registry's category order, then the owner's order inside each."""
    query = db.query(SystemOption)
    if category is not None:
        check_category(category)
        query = query.filter(SystemOption.category == category)
    rows = query.all()
    rows.sort(key=lambda r: (_category_position(r.category), r.sort_order, r.id))
    return rows


def get(db: Session, option_id: int) -> SystemOption:
    row = db.get(SystemOption, option_id)
    if row is None:
        raise AppError(404, "No such option.")
    return row


def _check_unique(db: Session, category: str, value: str, exclude_id: int | None = None) -> None:
    """Mirrors uq_system_option_value: trimmed and case-folded."""
    query = db.query(SystemOption.id).filter(
        SystemOption.category == category,
        func.lower(func.btrim(SystemOption.value)) == func.lower(value.strip()),
    )
    if exclude_id is not None:
        query = query.filter(SystemOption.id != exclude_id)
    if query.first() is not None:
        raise AppError(409, DUPLICATE)


def create(db: Session, payload) -> SystemOption:
    _check_unique(db, payload.category, payload.value)
    sort_order = payload.sort_order
    if sort_order is None:
        last = (
            db.query(func.max(SystemOption.sort_order))
            .filter(SystemOption.category == payload.category)
            .scalar()
        )
        sort_order = 0 if last is None else last + 1
    row = SystemOption(
        category=payload.category,
        value=payload.value,
        description=payload.description,
        remark=payload.remark,
        sort_order=sort_order,
    )
    db.add(row)
    db.commit()
    return get(db, row.id)


def update(db: Session, option_id: int, payload) -> SystemOption:
    row = get(db, option_id)
    sent = {field: getattr(payload, field) for field in payload.model_fields_set}
    if "value" in sent:
        _check_unique(db, row.category, sent["value"], exclude_id=row.id)
    for field, value in sent.items():
        setattr(row, field, value)
    db.commit()
    return get(db, option_id)


def delete(db: Session, option_id: int, expected_in_use: int) -> None:
    """Delete, with the count the page showed echoed back.

    On success the database does the rest: topic links cascade and
    `note.category_id` is set NULL (the foreign keys' ON DELETE).
    """
    row = get(db, option_id)
    actual = in_use(db, option_id)
    if actual != expected_in_use:
        raise StaleCountError("in_use", "links", expected_in_use, actual)
    db.delete(row)
    db.commit()


def fetch_in_category(db: Session, ids: list[int], category: str) -> list[SystemOption]:
    """The options `ids` name, in that order, or 422 naming the first bad id.

    An id that does not exist, and one that exists in another category, are
    both a malformed payload - the URL resolved; the body is wrong. A FK
    cannot see the category, so this is the only place that rule is held.
    Repeats collapse to one row.
    """
    wanted = list(dict.fromkeys(ids))
    if not wanted:
        return []
    found = {row.id: row for row in db.query(SystemOption).filter(SystemOption.id.in_(wanted))}
    label = OPTION_CATEGORIES[category].label
    for option_id in wanted:
        row = found.get(option_id)
        if row is None:
            raise AppError(422, f"No such option: {option_id}.")
        if row.category != category:
            raise AppError(
                422,
                f"Option {option_id} is a {row.category} option, not a {category} ({label}) option.",
            )
    return [found[i] for i in wanted]
