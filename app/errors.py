"""One error shape, and the backstop that keeps a constraint from being a 500.

Copied from `food`. On the wire every error is `{"detail": "<a sentence>"}`.
There is no machine-readable code field: one user, no translations, and the
HTTP status already says which kind of failure this is.

**Where a caller must ACT on an error, the error carries data beside the
detail** - not a code. `AppError` serialises its extras into the body, so a
dialog can say "this now removes 4, not 3" and re-offer the button instead of
telling the user to reload.

The `IntegrityError` handler is a BACKSTOP, not the mechanism. The schema and
service layers mirror each constraint so the ordinary path answers before the
database is touched; the backstop is what stops a missed one being a 500.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

# Classified by SQLSTATE rather than by constraint name, so a constraint added
# later is mapped by what kind of violation it is instead of by whether anyone
# remembered to add it here.
#
# 23503 is the split: the same foreign-key violation means "your payload names
# a row that does not exist" on a write and "something still references this
# row" on a delete.
CHECK_VIOLATION = "23514"
NOT_NULL_VIOLATION = "23502"
UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"

# A sentence per constraint we can name. Anything absent falls back to the
# generic line for its SQLSTATE.
CONSTRAINT_MESSAGES = {
    "ck_system_option_category": "An option's category must be one this app registers.",
    "uq_system_option_value": "That category already has that value.",
    "ck_note_has_a_name": "A note needs at least one name.",
    "ck_note_visibility": "Visibility is one of private, unlisted or public.",
    "uq_note_alias": "That note already carries that alias.",
    "ck_note_resource_has_a_url": "A resource needs a URL.",
    "uq_goal_code": "Another goal already has that code.",
    "ck_goal_has_a_name": "A goal needs at least one name.",
    "ck_goal_status": "A goal's status is one of planned, active or achieved.",
    "ck_goal_achieved_on_iff_achieved": "achieved_on is set only when the status is achieved.",
    "ck_stage_has_a_name": "A stage needs at least one name.",
    "ck_stage_status": "A stage's status is one of not_started, in_progress or passed.",
    "ck_stage_passed_on_iff_passed": "passed_on is set only when the status is passed.",
    "ck_stage_resource_has_a_url": "A resource needs a URL.",
}

GENERIC_MESSAGES = {
    CHECK_VIOLATION: "That change does not satisfy a rule on the data.",
    NOT_NULL_VIOLATION: "Something required was left empty.",
    UNIQUE_VIOLATION: "Something else already has that value.",
}


class AppError(Exception):
    """An error with a sentence, a status, and optionally data to act on."""

    def __init__(self, status_code: int, detail: str, **extras):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.extras = extras


class StaleCountError(AppError):
    """The count shown in a confirmation dialog is no longer true.

    Any delete that takes rows the user was shown a count of takes that count
    as a required parameter and raises this when it has moved. An optimistic
    check, not a lock: it guards a stale tab, which in a one-user app is the
    whole case.

    `expected` and `actual` ride on the body so the dialog can correct itself
    in place; `field` names which count moved, using the delete's
    query-parameter name.
    """

    def __init__(self, field: str, what: str, expected: int, actual: int):
        super().__init__(
            409,
            f"This now removes {actual} {what}, not {expected}. Check and confirm again.",
            field=field,
            expected=expected,
            actual=actual,
        )


def _sqlstate(exc: IntegrityError) -> str | None:
    return getattr(getattr(exc, "orig", None), "sqlstate", None) or getattr(
        getattr(exc, "orig", None), "pgcode", None
    )


def _constraint_name(exc: IntegrityError) -> str | None:
    diag = getattr(getattr(exc, "orig", None), "diag", None)
    return getattr(diag, "constraint_name", None)


def integrity_status(sqlstate: str | None, method: str) -> int:
    """The status a constraint violation answers with. See the note above."""
    if sqlstate in (CHECK_VIOLATION, NOT_NULL_VIOLATION):
        return 422
    if sqlstate == UNIQUE_VIOLATION:
        return 409
    if sqlstate == FOREIGN_KEY_VIOLATION:
        return 409 if method == "DELETE" else 422
    # Still the database refusing a change, not the server falling over.
    return 409


def install(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.detail, **exc.extras}
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        sqlstate = _sqlstate(exc)
        constraint = _constraint_name(exc)
        status = integrity_status(sqlstate, request.method)

        detail = CONSTRAINT_MESSAGES.get(constraint) or GENERIC_MESSAGES.get(sqlstate)
        if detail is None:
            detail = (
                "Something else still refers to this, so it cannot be removed."
                if status == 409 and request.method == "DELETE"
                else "The database refused that change."
            )

        logger.warning(
            "integrity error on %s %s: sqlstate=%s constraint=%s",
            request.method,
            request.url.path,
            sqlstate,
            constraint,
        )
        return JSONResponse(status_code=status, content={"detail": detail})

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception):
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500, content={"detail": "An unexpected server error occurred."}
        )
