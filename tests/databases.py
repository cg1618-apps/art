"""Test databases: one per run, one per scratch use, none with a fixed name.

The platform's rule (`docs/registry.md`, "How an app's tests use the shared
server"): what makes two test runs collide is a shared database NAME, not the
shared server. So every database a test touches is created here under a name
nobody else can hold, and dropped when its user is done with it. The pattern
is the media tracker's `tests/databases.py`.

Names are `art_test_<epoch>_<hex>`. The epoch is part of the unique suffix and
is what makes leftover cleanup safe: a database with no connections is only
dropped once it is older than LEFTOVER_AGE, so a run that has just created a
database and not yet connected to it - a migration test's scratch database
waits for an `alembic` subprocess to start - cannot lose it to a neighbour's
cleanup.

The server and credentials are the app's own settings with only the database
name swapped, so nothing here reads a name from `.env` and nothing carries a
password.
"""

import re
import time
import uuid
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

PREFIX = "art_test"
LEFTOVER_AGE = 2 * 60 * 60  # seconds
_NAME = re.compile(rf"^{PREFIX}_(\d+)_[0-9a-f]{{8}}$")


def new_name() -> str:
    """A database name no other run or test can be using."""
    return f"{PREFIX}_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def is_test_database(name: str) -> bool:
    return bool(_NAME.match(name))


def _require_test_database(name: str) -> None:
    if not is_test_database(name):
        raise ValueError(f"not a test database name, refusing to touch it: {name!r}")


def server_url(database: str) -> str:
    """The configured server, pointed at one named database.

    `render_as_string(hide_password=False)` rather than `str()`: SQLAlchemy's
    URL.__str__ masks the password as `***`, so str() hands back a URL that
    reaches the right host as the right user and fails authentication.

    `localhost` becomes `127.0.0.1`. On Windows it resolves to `::1` first,
    the platform's dev database listens on 127.0.0.1 only, and every new
    connection waits about 21 seconds before falling back - which the
    migration tests, opening several connections each, pay many times over.
    """
    from app.config import settings

    url = make_url(settings.sqlalchemy_database_url).set(database=database)
    if url.host == "localhost":
        url = url.set(host="127.0.0.1")
    return url.render_as_string(hide_password=False)


def _admin():
    return create_engine(server_url("postgres"), isolation_level="AUTOCOMMIT")


def create(name: str) -> None:
    _require_test_database(name)
    admin = _admin()
    try:
        with admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        admin.dispose()


def drop(name: str) -> None:
    """Drop one test database, ending any session still connected to it.

    WITH (FORCE) because a failed assertion can leave a connection open, and a
    plain DROP would then fail in teardown and bury the assertion that matters
    under an unrelated error.
    """
    _require_test_database(name)
    admin = _admin()
    try:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    finally:
        admin.dispose()


def drop_leftovers(now: float | None = None) -> list[str]:
    """Drop test databases a crashed or interrupted run left behind.

    Only names this module mints, only with no connections, and only once
    older than LEFTOVER_AGE - a database with connections, or a young one,
    belongs to a run in progress. Returns the names dropped.
    """
    now = time.time() if now is None else now
    admin = _admin()
    dropped = []
    try:
        with admin.connect() as conn:
            names = conn.execute(
                text(
                    "SELECT d.datname FROM pg_database d"
                    " WHERE d.datname LIKE :prefix AND NOT EXISTS ("
                    "   SELECT 1 FROM pg_stat_activity a WHERE a.datname = d.datname)"
                ),
                {"prefix": f"{PREFIX}\\_%"},
            ).scalars().all()
            for name in names:
                match = _NAME.match(name)
                if match and now - int(match.group(1)) > LEFTOVER_AGE:
                    # No FORCE: a connection that arrived since the query
                    # above makes this fail, which is the right outcome.
                    conn.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
                    dropped.append(name)
    finally:
        admin.dispose()
    return dropped


@contextmanager
def scratch():
    """A fresh, empty database for one use, dropped afterwards whatever
    happens. Yields its name; `server_url(name)` connects to it."""
    name = new_name()
    create(name)
    try:
        yield name
    finally:
        drop(name)
