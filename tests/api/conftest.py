"""Fixtures for anything that touches PostgreSQL. `food`'s, with art's names.

The schema is built with `Base.metadata.create_all`, NOT by running Alembic.
`tests/test_migrations_build_the_schema.py` covers the other side, by running
the real `alembic upgrade head` against a scratch database and comparing the
result with the models. Neither is optional.

Isolation is an outer transaction rolled back at teardown, with the session
joined to it via savepoints so that code under test may call `commit()` without
destroying the fixture rows around it.

`create_all` seeds nothing: the migration's option values are not part of the
model metadata, so every test starts with an empty `system_option` and makes
the options it needs with `make_option`.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# `models` is imported for the side effect of registering every model on
# Base.metadata before create_all runs; without it the test schema is empty.
from app import models  # noqa: F401
from app.config import settings
from app.database import Base

TEST_DATABASE = "art_test"


def _url(database: str) -> str:
    """The app's own connection settings with the database name swapped.

    Derived rather than hardcoded: the password is per-machine and is not
    something a test may carry.
    """
    return settings.sqlalchemy_database_url.rsplit("/", 1)[0] + f"/{database}"


@pytest.fixture(scope="session")
def test_engine():
    admin = create_engine(_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DATABASE} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {TEST_DATABASE}"))
    admin.dispose()

    engine = create_engine(_url(TEST_DATABASE))
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

    admin = create_engine(_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DATABASE} WITH (FORCE)"))
    admin.dispose()


@pytest.fixture
def db(test_engine):
    """A session whose every write is rolled back when the test ends.

    `join_transaction_mode="create_savepoint"` is load-bearing: without it a
    `rollback()` inside the code under test unwinds this outer transaction as
    well, and the fixture rows vanish mid-test with nothing to say why.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session = Session()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db):
    """A TestClient whose requests use the test's own rolled-back session.

    `raise_server_exceptions=False` so the registered handlers turn an
    exception into a response, and a test asserts the status a caller sees.
    """
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import create_app

    app = create_app()

    def request_session():
        """Hand out the test's session, and clean up after a refused request,
        which would otherwise fail the NEXT request with an unrelated 500."""
        try:
            yield db
        finally:
            if not db.is_active:
                db.rollback()

    app.dependency_overrides[get_db] = request_session
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_option(db):
    """A factory: `make_option("topic", "透視")` saves and returns one row."""
    from app.models import SystemOption

    def make(category: str, value: str, **fields):
        row = SystemOption(category=category, value=value, **fields)
        db.add(row)
        db.flush()
        return row

    return make


@pytest.fixture
def options(make_option):
    """One option of every category, so a category check has something to
    refuse.

    LOAD-BEARING for every wrong-category test: with only one category in the
    table, a check that never looked at the category would pass. Each refusal
    test that uses this has a mirror using the same fixture, so a green proves
    the check did the refusing.
    """
    return {
        "note_category": make_option("note_category", "名詞"),
        "other_note_category": make_option("note_category", "小技巧"),
        "topic": make_option("topic", "透視", description="空間的遠近"),
        "other_topic": make_option("topic", "人體"),
        "method": make_option("method", "速寫"),
        "other_method": make_option("method", "描寫", description="看著參考圖畫"),
        "source": make_option("source", "Character Art School"),
        "location": make_option("location", "台灣・家"),
        "tool": make_option("tool", "Clip Studio Paint"),
    }
