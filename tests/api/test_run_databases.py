"""One database per run, and nothing left behind (docs/testing.md, "One
database per run").

What makes two runs collide is a shared database NAME. These pin the two
halves of the rule: the run's database is its own, and a crashed run's
leftover is dropped by the next run - but never a database another run is
still using.
"""

import time

from sqlalchemy import create_engine, text

from tests import databases


def _exists(name: str) -> bool:
    admin = create_engine(databases.server_url("postgres"))
    try:
        with admin.connect() as conn:
            return bool(
                conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
                ).scalar()
            )
    finally:
        admin.dispose()


def _aged(seconds: float) -> str:
    """A name minted `seconds` ago, as a crashed run's would have been."""
    suffix = databases.new_name().rsplit("_", 1)[1]
    return f"{databases.PREFIX}_{int(time.time() - seconds)}_{suffix}"


def test_the_run_database_is_not_a_fixed_name(test_engine):
    name = test_engine.url.database
    assert databases.is_test_database(name), name
    assert name != "art_test"


def test_a_leftover_with_no_connections_is_dropped():
    name = _aged(databases.LEFTOVER_AGE + 60)
    databases.create(name)
    try:
        assert name in databases.drop_leftovers()
        assert not _exists(name)
    finally:
        databases.drop(name)


def test_a_leftover_somebody_is_connected_to_is_left_alone():
    """The mirror: same age, same prefix, one open connection."""
    name = _aged(databases.LEFTOVER_AGE + 60)
    databases.create(name)
    engine = create_engine(databases.server_url(name))
    try:
        with engine.connect():
            assert name not in databases.drop_leftovers()
            assert _exists(name)
    finally:
        engine.dispose()
        databases.drop(name)


def test_a_young_database_with_no_connections_is_left_alone():
    """A run that has created its database and not yet connected to it is
    not a leftover - the age is what tells the two apart."""
    name = databases.new_name()
    databases.create(name)
    try:
        assert name not in databases.drop_leftovers()
        assert _exists(name)
    finally:
        databases.drop(name)


def test_a_scratch_database_is_dropped_after_use():
    with databases.scratch() as name:
        assert _exists(name)
    assert not _exists(name)
