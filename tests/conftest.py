"""Test-wide fixtures.

`app.config.settings` is a module-level object built from the environment at
import time, so a test that monkeypatches the environment and reloads the
module leaves the reloaded object behind for every later test in the session.

The reload has to happen AFTER monkeypatch has undone its changes. Fixture
teardown is LIFO, and an autouse fixture is set up before the function-scoped
monkeypatch it shares a test with — so this fixture's teardown runs last, with
the real environment restored, which is exactly the window the reload needs.
"""

import importlib

import pytest


@pytest.fixture(autouse=True)
def restore_config_defaults():
    yield
    from app import config

    importlib.reload(config)


@pytest.fixture(scope="session")
def test_databases():
    """Once per run, before the run's first database: drop what crashed runs
    left behind (`tests/databases.py` says which ones count).

    Requested by every fixture that creates a database, and by nothing else,
    so a run of `tests/unit` never opens a connection to PostgreSQL.
    """
    from tests import databases

    databases.drop_leftovers()
    return databases


@pytest.fixture
def scratch_database(test_databases):
    """An empty database of this test's own, dropped afterwards. Yields its
    URL, for a test that builds the chain itself."""
    with test_databases.scratch() as name:
        yield test_databases.server_url(name)
