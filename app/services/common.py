"""Write rules more than one service holds. Each refuses before anything is
assigned, so a refused save changes nothing - and an autoflush cannot write a
half-applied row."""

from datetime import date

from app.errors import AppError
from app.schemas.common import NAME_FIELDS


def merged(row, sent: dict, field: str):
    """What `field` will hold once `sent` is applied to `row` (None: a row
    not yet created)."""
    if field in sent:
        return sent[field]
    return getattr(row, field) if row is not None else None


def require_a_name(row, sent: dict, message: str) -> None:
    """`ck_<table>_has_a_name` against the MERGED row: a PATCH may clear one
    name while another remains, but not the last one."""
    if not any(merged(row, sent, field) for field in NAME_FIELDS):
        raise AppError(422, f"{message}.")


def check_dated_status(row, sent: dict, *, done: str, date_field: str) -> None:
    """`ck_<table>_<date>_iff_<done>`, for a status that may carry a date.

    Setting the status away from `done` clears the date, unless the same save
    sends a date - which, with any status but `done`, is a 422 rather than a
    silent drop. `done` itself may leave the date NULL. Mutates `sent`.
    """
    if "status" in sent and sent["status"] != done and date_field not in sent:
        sent[date_field] = None
    stamped: date | None = merged(row, sent, date_field)
    if stamped is not None and merged(row, sent, "status") != done:
        raise AppError(422, f"{date_field} is set only when the status is {done}.")


def apply_aliases(owner, alias_model, values: list[str]) -> None:
    """Reconcile `owner.aliases` with `values`, by value.

    A kept alias keeps its row, so a save that changes nothing deletes and
    re-inserts nothing (and cannot trip `uq_<table>_alias` against the row it
    is replacing). Shared by every row with an `<table>_alias` table.
    """
    wanted = list(dict.fromkeys(values))
    owner.aliases = [row for row in owner.aliases if row.value in wanted]
    kept = {row.value for row in owner.aliases}
    owner.aliases.extend(alias_model(value=v) for v in wanted if v not in kept)
