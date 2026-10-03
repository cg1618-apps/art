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


ROADMAP_ORDER = """
    SELECT goal.code, goal.status, stage.name_en, stage.status, stage.position
      FROM stage JOIN goal ON goal.id = stage.goal_id
     ORDER BY goal.position, goal.id, stage.position, stage.id
"""


def test_the_roadmap_is_seeded_in_order(scratch_database):
    """Six levels, sixteen stages numbered 0-15 in the spec's order, L0
    active and every stage not started. The full text is in the migration;
    two strings are compared verbatim here as a check on the copying."""
    _upgrade(scratch_database)

    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        goals = conn.execute(
            text("SELECT code, name_cn, name_en, status, position FROM goal ORDER BY position")
        ).all()
        stages = conn.execute(text(ROADMAP_ORDER)).all()
        l0_description = conn.execute(
            text("SELECT description FROM goal WHERE code = 'L0'")
        ).scalar()
        effects_test = conn.execute(text("SELECT test FROM stage WHERE name_en = 'Effects'")).scalar()
    engine.dispose()

    assert [(c, cn, en, s) for c, cn, en, s, _ in goals] == [
        ("L0", "基礎", "Foundations", "active"),
        ("L1", "人體", "Figure", "planned"),
        ("L2", "角色", "Character", "planned"),
        ("L3", "場景", "Scene", "planned"),
        ("L4", "上色", "Colour", "planned"),
        ("L5", "插畫", "Illustration", "planned"),
    ]
    assert [p for *_, p in goals] == list(range(6))

    assert len(stages) == 16
    # The derived number is the place in this order: 0 to 15.
    assert [(code, name) for code, _, name, _, _ in stages] == [
        ("L0", "Clip Studio Paint setup"),
        ("L0", "Lines and shapes"),
        ("L0", "Form in space"),
        ("L1", "Proportion"),
        ("L1", "Gesture to mannequin"),
        ("L1", "Figure in perspective"),
        ("L2", "Major muscle masses"),
        ("L2", "Head, face, expression"),
        ("L2", "Hands and feet"),
        ("L2", "Finishing"),
        ("L3", "Environment perspective"),
        ("L3", "Composition and character in scene"),
        ("L4", "Value and light"),
        ("L4", "Colour"),
        ("L5", "Full pieces and creatures"),
        ("L5", "Effects"),
    ]
    assert {status for _, _, _, status, _ in stages} == {"not_started"}
    positions: dict[str, list[int]] = {}
    for code, _, _, _, position in stages:
        positions.setdefault(code, []).append(position)
    assert all(p == list(range(len(p))) for p in positions.values()), positions

    assert l0_description == "能穩定地畫出線條與基本形狀，並把方塊、圓柱、球體放進透視空間。"
    assert effects_test == "一張有火球的角色插畫。"


def test_the_roadmap_seed_is_idempotent(scratch_database):
    """Running the seed again over a seeded database adds nothing."""
    import importlib.util

    _upgrade(scratch_database)
    spec = importlib.util.spec_from_file_location(
        "goals_and_roadmap", ROOT / "alembic" / "versions" / "0003_goals_and_roadmap.py"
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine(scratch_database)
    with engine.begin() as conn:
        migration.seed(conn)
    with engine.connect() as conn:
        counts = conn.execute(
            text("SELECT (SELECT count(*) FROM goal), (SELECT count(*) FROM stage)")
        ).one()
    engine.dispose()
    assert tuple(counts) == (6, 16)


def test_goals_and_roadmap_downgrade_and_upgrade_again(scratch_database):
    """Down to 0002 drops the roadmap's tables and nothing else; up again
    re-seeds it."""
    _upgrade(scratch_database)
    _downgrade(scratch_database, "0002_notes_and_options")

    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names()) - {"alembic_version"}
    engine.dispose()
    assert tables == {"system_option", "note", "note_alias", "note_resource", "note_topic"}, tables

    _upgrade(scratch_database)
    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        counts = conn.execute(
            text("SELECT (SELECT count(*) FROM goal), (SELECT count(*) FROM stage)")
        ).one()
    engine.dispose()
    assert tuple(counts) == (6, 16)


RECORD_MODULE_TABLES = {
    "exercise",
    "exercise_alias",
    "exercise_resource",
    "exercise_topic",
    "drill",
    "drill_source_link",
    "drill_resource",
    "record",
    "record_reference",
}


def _counts(database_url: str) -> tuple[int, int]:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        counts = conn.execute(
            text("SELECT (SELECT count(*) FROM exercise), (SELECT count(*) FROM drill)")
        ).one()
    engine.dispose()
    return tuple(counts)


def test_the_exercises_drills_and_their_options_are_seeded(scratch_database):
    """24 exercises and 57 drills, three new categories with their values.
    The full text is in the migration; a few strings are compared verbatim
    here as a check on the copying."""
    _upgrade(scratch_database)

    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        options = conn.execute(
            text(
                "SELECT category, value FROM system_option"
                " WHERE category IN ('source', 'location', 'tool')"
                " ORDER BY category, sort_order"
            )
        ).all()
        exercises = {
            name_en: (name_cn, stage, description)
            for name_cn, name_en, stage, description in conn.execute(
                text(
                    "SELECT exercise.name_cn, exercise.name_en, stage.name_cn, exercise.description"
                    "  FROM exercise LEFT JOIN stage ON stage.id = exercise.stage_id"
                )
            )
        }
        drills = conn.execute(
            text(
                "SELECT exercise.name_en, drill.name, source.value, drill.unit, drill.target,"
                "       drill.suggested_minutes, drill.frequency, drill.instructions,"
                "       drill.position"
                "  FROM drill JOIN exercise ON exercise.id = drill.exercise_id"
                "  LEFT JOIN system_option source ON source.id = drill.source_id"
                " ORDER BY exercise.id, drill.position"
            )
        ).all()
        resources = conn.execute(
            text(
                "SELECT exercise.name_en, r.name, r.url FROM exercise_resource r"
                "  JOIN exercise ON exercise.id = r.exercise_id ORDER BY exercise.id"
            )
        ).all()
        topics = conn.execute(text("SELECT count(*) FROM exercise_topic")).scalar()
    engine.dispose()

    by_category: dict[str, list[str]] = {}
    for category, value in options:
        by_category.setdefault(category, []).append(value)
    assert by_category == {
        "source": [
            "Character Art School",
            "Character Art School: Coloring",
            "Manga Art School",
            "Perspective Art School",
            "自訂",
            "其他",
        ],
        "location": ["台灣・家", "美國・家"],
        "tool": ["Clip Studio Paint", "Procreate", "紙筆"],
    }

    assert len(exercises) == 24
    assert len(drills) == 57
    assert topics == 0  # the owner tags them

    assert exercises["Lines"] == ("線條", "線條與形狀", "穩定的直線與曲線，用手肘和肩膀畫，不用手腕。")
    assert exercises["Gesture drawing"] == (
        "動態速寫",
        None,
        "限時抓動態。每個等級都練，所以不屬於任何階段。",
    )
    assert exercises["Hair"][1] == "完稿：頭髮、衣服、配件"
    assert sum(stage is None for _, stage, _ in exercises.values()) == 4

    by_name = {row[1]: row for row in drills}
    assert by_name["幾何概括+翻轉"] == (
        "Basic forms",
        "幾何概括+翻轉",
        "自訂",
        "張",
        10,
        30,
        "每天",
        "隨機找有獨立物體的圖，用基本幾何（可以變形，例如橢圓）概括物體的結構，物體本身和位置都要準確。"
        "再把物體裝進盒子，根據概括畫出翻轉後的版本，每個概括 2 個。",
        1,
    )
    assert by_name["Life Gestures"][2:7] == (
        "Character Art School",
        "頁",
        1,
        5,
        "daily / forever if possible",
    )
    # A blank in the sheet stays NULL.
    assert by_name["Complete Environment Piece"][5] is None
    assert by_name["Character Drawing"][6] is None
    assert by_name["Static & Dynamic Forms"][7] is None

    positions: dict[str, list[int]] = {}
    for exercise, *_, position in drills:
        positions.setdefault(exercise, []).append(position)
    assert all(p == list(range(len(p))) for p in positions.values()), positions

    assert resources == [
        ("Mannequin", "Line of Action", "https://line-of-action.com/"),
        ("Gesture drawing", "Line of Action", "https://line-of-action.com/"),
    ]


def test_the_exercise_seed_is_idempotent(scratch_database):
    import importlib.util

    _upgrade(scratch_database)
    spec = importlib.util.spec_from_file_location(
        "exercises_and_records", ROOT / "alembic" / "versions" / "0004_exercises_and_records.py"
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine(scratch_database)
    with engine.begin() as conn:
        migration.seed(conn)
    with engine.connect() as conn:
        extra = conn.execute(
            text(
                "SELECT (SELECT count(*) FROM system_option"
                "         WHERE category IN ('source', 'location', 'tool')),"
                "       (SELECT count(*) FROM exercise_resource)"
            )
        ).one()
    engine.dispose()
    assert _counts(scratch_database) == (24, 57)
    assert tuple(extra) == (11, 2)


def test_a_renamed_stage_leaves_its_exercises_with_none_rather_than_failing(scratch_database):
    _upgrade(scratch_database, "0003_goals_and_roadmap")
    engine = create_engine(scratch_database)
    with engine.begin() as conn:
        conn.execute(text("UPDATE stage SET name_cn = '比例（改）' WHERE name_cn = '比例'"))
    engine.dispose()

    _upgrade(scratch_database)
    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        stages = dict(
            conn.execute(
                text(
                    "SELECT name_en, stage_id FROM exercise"
                    " WHERE name_en IN ('Body proportion', 'Mannequin', 'Lines')"
                )
            ).all()
        )
    engine.dispose()
    assert stages["Body proportion"] is None
    assert stages["Mannequin"] is None
    assert stages["Lines"] is not None  # the mirror: an unrenamed stage is found
    assert _counts(scratch_database) == (24, 57)


def test_exercises_and_records_downgrade_and_upgrade_again(scratch_database):
    """Down to 0003 drops the module's tables and its categories' values, and
    puts the old category check back; up again re-seeds it."""
    _upgrade(scratch_database)
    _downgrade(scratch_database, "0003_goals_and_roadmap")

    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        categories = set(
            conn.execute(text("SELECT DISTINCT category FROM system_option")).scalars()
        )
    assert not tables & RECORD_MODULE_TABLES, tables & RECORD_MODULE_TABLES
    assert {"goal", "stage", "system_option", "note"} <= tables
    assert categories == {"note_category", "topic", "method"}

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("INSERT INTO system_option (category, value) VALUES ('tool', 'x')"))
    engine.dispose()

    _upgrade(scratch_database)
    assert _counts(scratch_database) == (24, 57)


def test_timer_downgrade_and_upgrade_again(scratch_database):
    """Down to 0004 drops `active_timer` and nothing else; up again brings
    it back with its singleton index."""
    _upgrade(scratch_database)
    _downgrade(scratch_database, "0004_exercises_and_records")

    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
    engine.dispose()
    assert "active_timer" not in tables
    assert RECORD_MODULE_TABLES <= tables, RECORD_MODULE_TABLES - tables

    _upgrade(scratch_database)
    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        indexes = {ix["name"]: ix for ix in inspect(conn).get_indexes("active_timer")}
    engine.dispose()
    assert indexes["uq_active_timer_single"]["unique"]


def test_the_migrated_timer_holds_at_most_one_row(scratch_database):
    """`create_all` builds the API tests' singleton index from the model; this
    is the migration's own. The first insert is the mirror."""
    from sqlalchemy.exc import IntegrityError

    _upgrade(scratch_database)
    engine = create_engine(scratch_database)
    insert = text("INSERT INTO active_timer (mode, running_since) VALUES ('stopwatch', now())")
    with engine.begin() as conn:
        conn.execute(insert)
    with pytest.raises(IntegrityError, match="uq_active_timer_single"), engine.begin() as conn:
        conn.execute(insert)
    engine.dispose()


def _note_columns(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        columns = {c["name"] for c in inspect(conn).get_columns("note")}
    engine.dispose()
    return columns


def test_note_name_keeps_the_first_slot_and_moves_the_other_names_to_the_remark(
    scratch_database,
):
    """0007's data path, on notes written at 0006: every name typed survives,
    either as the name or in the remark's 其他名稱 line."""
    _upgrade(scratch_database, "0006_timer_draft")
    engine = create_engine(scratch_database)
    with engine.begin() as conn:
        def note(name_cn, name_en, name_alt, remark=None, aliases=()):
            note_id = conn.execute(
                text(
                    "INSERT INTO note (name_cn, name_en, name_alt, remark)"
                    " VALUES (:cn, :en, :alt, :remark) RETURNING id"
                ),
                {"cn": name_cn, "en": name_en, "alt": name_alt, "remark": remark},
            ).scalar()
            for value in aliases:
                conn.execute(
                    text("INSERT INTO note_alias (note_id, value) VALUES (:id, :value)"),
                    {"id": note_id, "value": value},
                )
            return note_id

        only_cn = note("透視", None, None)
        full = note("消失點", "vanishing point", "VP", remark="再補例子", aliases=["滅點", "VP"])
        only_en = note(None, "gesture", None, aliases=["動態"])
        only_alt = note(None, None, "GD")
    engine.dispose()

    _upgrade(scratch_database, "0007_note_name")
    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        rows = {
            note_id: (name, remark)
            for note_id, name, remark in conn.execute(text("SELECT id, name, remark FROM note"))
        }
        tables = set(inspect(conn).get_table_names())
    engine.dispose()

    assert rows[only_cn] == ("透視", None)  # nothing else to keep: the remark is untouched
    # VP is both a slot and an alias: listed once.
    assert rows[full] == ("消失點", "再補例子\n其他名稱：vanishing point、VP、滅點")
    assert rows[only_en] == ("gesture", "其他名稱：動態")
    assert rows[only_alt] == ("GD", None)
    assert "note_alias" not in tables
    assert not {"name_cn", "name_en", "name_alt"} & _note_columns(scratch_database)

    _downgrade(scratch_database, "0006_timer_draft")
    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        back = dict(conn.execute(text("SELECT id, name_cn FROM note")).all())
        tables = set(inspect(conn).get_table_names())
    engine.dispose()
    assert back == {only_cn: "透視", full: "消失點", only_en: "gesture", only_alt: "GD"}
    assert "note_alias" in tables
    assert "name" not in _note_columns(scratch_database)


def test_the_migrated_note_name_refuses_a_blank(scratch_database):
    """The migration's own check, which `create_all` never builds. The first
    insert is the mirror."""
    from sqlalchemy.exc import IntegrityError

    _upgrade(scratch_database)
    engine = create_engine(scratch_database)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO note (name) VALUES ('透視')"))
    with pytest.raises(IntegrityError, match="ck_note_name_not_blank"), engine.begin() as conn:
        conn.execute(text("INSERT INTO note (name) VALUES ('  ')"))
    engine.dispose()


def test_references_downgrade_and_upgrade_again(scratch_database):
    """Down to 0007 drops the two tables and the category's values, and puts
    the old category check back; up again accepts the category."""
    from sqlalchemy.exc import IntegrityError

    _upgrade(scratch_database)
    engine = create_engine(scratch_database)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO system_option (category, value) VALUES ('reference_group', '表情')")
        )
    engine.dispose()

    _downgrade(scratch_database, "0007_note_name")
    engine = create_engine(scratch_database)
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        groups = conn.execute(
            text("SELECT count(*) FROM system_option WHERE category = 'reference_group'")
        ).scalar()
    assert not {"reference", "reference_group"} & tables
    assert "note" in tables
    assert groups == 0
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            text("INSERT INTO system_option (category, value) VALUES ('reference_group', 'x')")
        )
    engine.dispose()

    _upgrade(scratch_database)
    engine = create_engine(scratch_database)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO system_option (category, value) VALUES ('reference_group', 'x')")
        )
    engine.dispose()
