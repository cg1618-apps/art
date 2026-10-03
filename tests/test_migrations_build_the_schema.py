"""The migration chain must build from nothing.

The media tracker ran for 145 revisions with a chain that could not: its
initial revision aborted its transaction on an empty database and rolled back
to zero tables, unnoticed because the test fixtures built their schema with
create_all and never ran Alembic. This test is what makes that impossible here,
and it is written before there is a single table to build.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

# `models` is imported for its side effect of registering every table on
# Base.metadata. Without it the comparisons below run against an empty
# metadata and pass vacuously - or pass only because some other test module
# happened to import the models first.
from app import models  # noqa: F401
from app.config import settings
from app.database import Base

ROOT = Path(__file__).resolve().parents[1]


def head_revision() -> str:
    """The chain's head, read from the revision files.

    Derived, never written as a literal. These tests used to compare against
    "0001_baseline", which meant the FIRST real migration this app ever added
    would fail two tests that have nothing to do with it - and the failure
    would name a revision id rather than the thing that was wrong.
    """
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(ROOT / "alembic.ini"))
    # script_location is relative to the cwd, not to the ini file, so an
    # absolute ini path is not enough on its own. Same reason app/routers
    # /health.py overrides it.
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    heads = ScriptDirectory.from_config(cfg).get_heads()
    assert len(heads) == 1, f"expected one head, found {heads}"
    return heads[0]


def _admin_url(database: str) -> str:
    """settings.sqlalchemy_database_url with only the trailing db name swapped.

    The scratch-database test needs an administrative connection, but it may
    not assume the shared PostgreSQL's superuser password - that value is
    per-machine and not something a test should hardcode. Deriving it from
    the app's own settings means the test works wherever the app itself
    would.
    """
    base = settings.sqlalchemy_database_url
    return base.rsplit("/", 1)[0] + f"/{database}"


@pytest.fixture
def scratch_database():
    """A database created for this test and dropped afterwards."""
    admin = create_engine(_admin_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS art_migration_test"))
        conn.execute(text("CREATE DATABASE art_migration_test"))
    yield _admin_url("art_migration_test")
    # WITH (FORCE) because the test reads the scratch database back, and a
    # failed assertion leaves that connection open - a plain DROP would then
    # fail in teardown and bury the assertion that actually matters under an
    # unrelated error.
    with admin.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS art_migration_test WITH (FORCE)"))


def test_upgrade_head_runs_against_an_empty_database(scratch_database):
    env = dict(os.environ)
    env["DATABASE_URL"] = scratch_database
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    # A return code on its own says nothing about WHERE the run landed. With
    # 0001_baseline empty, a run that ignored DATABASE_URL and stamped the
    # developer's real `art` database would exit 0 and this test would stay
    # green. Reading the scratch database back is what pins it.
    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        stamped = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert stamped == head_revision()

        # Bites from 0002_notes_and_options onwards: a revision that declares
        # a model without creating its table fails here.
        tables = set(inspect(conn).get_table_names())
        assert tables >= set(Base.metadata.tables), set(Base.metadata.tables) - tables
    engine.dispose()


def test_there_is_exactly_one_head():
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 1, result.stdout
    # The command's answer must agree with the revision files' own. Both are
    # Alembic's, so this is not much of a cross-check - but asserting a
    # literal id here is what made every future migration fail this test.
    assert head_revision() in lines[0], result.stdout


def _upgrade(database_url: str, target: str = "head") -> None:
    env = dict(os.environ)
    env["DATABASE_URL"] = database_url
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", target],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def _downgrade(database_url: str, target: str) -> None:
    env = dict(os.environ)
    env["DATABASE_URL"] = database_url
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", target],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_the_migrated_schema_matches_the_models(scratch_database):
    """The migration and the models must describe the same database.

    The two are written by hand and separately - a migration may not import
    from `app.models` - so nothing but this makes them agree. The table-name
    check above passes a forgotten index, column or foreign key straight
    through; `tests/api/conftest.py` builds with `create_all` and never runs
    the migration at all. `food`'s test, adopted.
    """
    _upgrade(scratch_database)

    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        differences = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    engine.dispose()

    assert differences == [], differences


def test_the_option_values_are_seeded_in_order(scratch_database):
    """`create_all` seeds nothing, so the API tests cannot see the seed; this
    is the only test that does. Method descriptions are compared verbatim."""
    _upgrade(scratch_database)

    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT category, value, description, sort_order FROM system_option"
                " ORDER BY category, sort_order"
            )
        ).all()
    engine.dispose()

    by_category: dict[str, list] = {}
    for category, value, description, sort_order in rows:
        by_category.setdefault(category, []).append((value, description, sort_order))

    assert [v for v, _, _ in by_category["note_category"]] == ["名詞", "知識", "小技巧", "建議"]
    assert [v for v, _, _ in by_category["topic"]] == [
        "線條", "形狀", "透視", "比例", "人體", "動態", "構圖", "光影", "色彩", "特效",
    ]
    assert [(v, d) for v, d, _ in by_category["method"]] == [
        ("臨摹", "直接在參考圖上方描繪，盡量完整還原。（很少使用）"),
        ("重現", "不疊在參考圖上，看著參考圖盡量完整還原整張圖，例如動畫截圖。屬於描寫的一種。"),
        ("描寫", "看著參考圖畫，不疊在參考圖上。不要求完整還原。"),
        ("速寫", "限時快速畫，抓動態和大形，不追求細節。"),
        ("同人創作", "以既有角色或作品為題材的創作：構圖和姿勢是自己的，對象是別人的。"),
        ("原創創作", "原創題材，例如自己的原創角色。可以使用參考資料。"),
        ("隨便畫", "沒有特定目標，想畫什麼就畫什麼。"),
    ]
    for values in by_category.values():
        assert [s for _, _, s in values] == list(range(len(values)))


def test_notes_and_options_downgrade_and_upgrade_again(scratch_database):
    """The downgrade drops everything it created, so the platform's rollback
    can take it back and a later deploy can bring it forward again."""
    _upgrade(scratch_database)
    _downgrade(scratch_database, "0001_baseline")

    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names()) - {"alembic_version"}
    engine.dispose()
    assert tables == set(), tables

    _upgrade(scratch_database)
