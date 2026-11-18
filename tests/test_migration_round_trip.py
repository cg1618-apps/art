"""The release must come back.

`test_migrations_build_the_schema.py` proves the chain builds FORWARD. This
proves the RELEASE reverses: it downgrades to the revision `origin/main` is at
- what the platform's rollback does to a release that fails - upgrades back to
head, and compares the schema with the one it started from.

To main's revision rather than one step, because concurrent sessions put
several revisions into one release, and reversing only the head would leave
every earlier one in it unexercised until the day a rollback needs it. When the
branch holds no revision beyond main, the range is the one step below the head
(`-1`). See the platform's `docs/registry.md`, "The round trip covers the
release, not one step".
"""

import subprocess
import warnings
from pathlib import Path

from sqlalchemy import create_engine, text

from tests.revisions import ROOT, head_revision, run_alembic, script_directory

VERSIONS = "alembic/versions/"

# Every named object and every column, in one comparable set. Names rather
# than an inspector's dicts so the failure message lists what moved.
SCHEMA_SQL = text(
    """
    SELECT 'table:' || c.relname || ':' || c.relkind::text
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
    UNION ALL
    SELECT 'constraint:' || conrelid::regclass || ':' || conname || ':'
           || pg_get_constraintdef(oid)
      FROM pg_constraint WHERE connamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'index:' || indexname || ':' || indexdef
      FROM pg_indexes WHERE schemaname = 'public'
    UNION ALL
    SELECT 'column:' || table_name || '.' || column_name || ':' || data_type || ':'
           || is_nullable || ':' || coalesce(column_default, '-')
      FROM information_schema.columns WHERE table_schema = 'public'
    """
)


def release_base(head: str, parent: dict[str, str | None], on_main: set[str] | None) -> str:
    """The downgrade target a rollback of this release would reach.

    Walks down from `head` through every revision `main` does not hold and
    stops at the first one it does - main's head. When `head` is itself on
    main, or `on_main` is unknown (None), the range is one step: `-1`.
    """
    if on_main is None or head in on_main:
        return "-1"
    revision = head
    while revision not in on_main:
        below = parent[revision]
        if below is None:
            return "base"  # the whole chain is new: main holds none of it
        revision = below
    return revision


def _main_revision_files() -> set[str] | None:
    """Basenames of the revision files on `origin/main`, or None if this
    checkout cannot see `origin/main`.

    A revision is identified by its file rather than by parsing the tree's
    ids: the same file on both sides is the same revision, and a file only
    this branch holds is one the release adds. CI checks out the whole history
    (`fetch-depth: 0`), which brings `origin/main` with it.
    """
    result = subprocess.run(
        ["git", "ls-tree", "--name-only", "origin/main", VERSIONS],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return {Path(line).name for line in result.stdout.splitlines()}


def release_range() -> tuple[str, str]:
    """(head, target) for this checkout against origin/main."""
    head = head_revision()
    files = _main_revision_files()
    parent, on_main = {}, set()
    for rev in script_directory().walk_revisions():
        assert not isinstance(rev.down_revision, tuple), f"merge revision {rev.revision}"
        parent[rev.revision] = rev.down_revision
        if files is not None and Path(rev.path).name in files:
            on_main.add(rev.revision)
    if files is None:
        warnings.warn(
            "origin/main is not readable here (run `git fetch origin`); "
            "the round trip falls back to one step",
            stacklevel=2,
        )
        return head, "-1"
    return head, release_base(head, parent, on_main)


def _schema(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            return {row[0] for row in conn.execute(SCHEMA_SQL)}
    finally:
        engine.dispose()


def test_the_release_survives_a_downgrade_and_a_second_upgrade(scratch_database):
    head, target = release_range()
    up = run_alembic(scratch_database, "upgrade", "head")
    assert up.returncode == 0, up.stderr

    before = _schema(scratch_database)
    # Both sides of a set comparison are satisfied by two empty sets.
    assert len(before) > 100, "the migrated schema is nearly empty; this check is vacuous"

    down = run_alembic(scratch_database, "downgrade", target)
    assert down.returncode == 0, f"downgrading {head} to {target} failed:\n{down.stderr}"
    # The downgrade must actually have left the head, or the round trip proved
    # nothing. The stamp, not the schema: a data-only revision changes no
    # object and is still in the range.
    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        stamped = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    engine.dispose()
    assert stamped != head, f"downgrading to {target} left the database at {head}"

    again = run_alembic(scratch_database, "upgrade", "head")
    assert again.returncode == 0, again.stderr

    after = _schema(scratch_database)
    assert after == before, (
        "the round trip did not restore the schema.\n"
        f"lost: {sorted(before - after)}\ngained: {sorted(after - before)}"
    )


# A chain a <- b <- c <- d. Pure: no database, no git.
CHAIN = {"a": None, "b": "a", "c": "b", "d": "c"}


def test_a_release_of_two_revisions_goes_back_to_mains_head():
    assert release_base("d", CHAIN, {"a", "b"}) == "b"


def test_a_release_of_one_revision_goes_back_one():
    assert release_base("c", CHAIN, {"a", "b"}) == "b"


def test_nothing_beyond_main_falls_back_to_one_step():
    assert release_base("b", CHAIN, {"a", "b"}) == "-1"


def test_an_unreadable_main_falls_back_to_one_step():
    assert release_base("d", CHAIN, None) == "-1"


def test_a_chain_main_holds_none_of_goes_back_to_base():
    assert release_base("d", CHAIN, set()) == "base"
