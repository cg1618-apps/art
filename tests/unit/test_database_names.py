"""The names `tests/databases.py` mints, and the names it refuses to touch.

No PostgreSQL: every refusal here happens before a connection is opened, which
is the point - a helper that drops databases must decide what it may drop
without asking the server.
"""

import re

import pytest

from tests import databases


def test_a_new_name_is_the_apps_prefix_and_a_unique_suffix():
    name = databases.new_name()
    assert re.fullmatch(r"art_test_\d+_[0-9a-f]{8}", name), name


def test_two_new_names_differ():
    assert databases.new_name() != databases.new_name()


@pytest.mark.parametrize("name", ["art", "art_test", "postgres", "media_test_1_abcdef12"])
def test_drop_refuses_a_name_it_did_not_mint(name):
    with pytest.raises(ValueError, match="not a test database"):
        databases.drop(name)


@pytest.mark.parametrize("name", ["art", "art_test"])
def test_create_refuses_a_name_it_did_not_mint(name):
    with pytest.raises(ValueError, match="not a test database"):
        databases.create(name)


def test_a_minted_name_is_accepted():
    """The mirror of the refusals: without it, a check that refused every
    name would pass them all."""
    assert databases.is_test_database(databases.new_name())


def test_localhost_is_reached_over_ipv4(monkeypatch):
    """Windows tries ::1 first and the dev database listens on 127.0.0.1
    only, so a `localhost` URL waits ~21 s per connection before falling
    back."""
    from app.config import settings

    monkeypatch.setattr(settings, "database_url", "postgresql://u:p@localhost:5432/art")
    assert databases.server_url("x") == "postgresql://u:p@127.0.0.1:5432/x"


def test_any_other_host_is_kept(monkeypatch):
    """The mirror: CI's and the box's hosts are not rewritten."""
    from app.config import settings

    monkeypatch.setattr(settings, "database_url", "postgresql://u:p@db:5432/art")
    assert databases.server_url("x") == "postgresql://u:p@db:5432/x"
