"""What a pull request into `dev` runs in its own CI run (scripts/pr_tests.py).

Pure: the changed paths and the files' text are handed in, so no git and no
PostgreSQL. The merge queue runs the full suite; these pin what the pull
request's own, faster run may leave to it.
"""

from scripts.pr_tests import ALWAYS, MIGRATION_GUARDS, select

TESTS = [
    "tests/unit/test_config.py",
    "tests/api/test_notes.py",
    "tests/api/test_timer.py",
    "tests/test_migrations_build_the_schema.py",
    "tests/test_migration_round_trip.py",
    "tests/test_seed_migration.py",
    "tests/test_other_migration.py",
]

FILES = {
    "alembic/versions/0009_schedule.py": 'revision = "0009_schedule"\n',
    "tests/test_seed_migration.py": 'revision_before("0009_schedule")\n',
    "tests/test_other_migration.py": 'revision_before("0008_references")\n',
}


def _select(*changed):
    return select(list(changed), FILES.get, TESTS)


def test_a_route_change_runs_the_unit_tier_and_the_tests_it_touches():
    assert _select("app/routers/notes.py", "tests/api/test_notes.py") == [
        *ALWAYS,
        "tests/api/test_notes.py",
    ]


def test_a_frontend_change_runs_the_unit_tier_alone():
    assert _select("frontend/src/App.jsx") == ALWAYS


def test_a_changed_unit_test_is_already_covered_by_the_unit_tier():
    assert _select("tests/unit/test_config.py") == ALWAYS


def test_a_deleted_test_file_is_not_selected():
    """A path in the diff that no longer exists at the head would make pytest
    error on a missing file."""
    assert _select("tests/api/test_gone.py") == ALWAYS


def test_a_new_revision_runs_the_guards_and_its_own_tests_only():
    """The mirror is in the same assertion: test_other_migration.py names
    another revision and must not be selected for this one."""
    assert _select("alembic/versions/0009_schedule.py") == [
        *ALWAYS,
        *MIGRATION_GUARDS,
        "tests/test_seed_migration.py",
    ]


def test_a_model_change_runs_the_migration_guards():
    assert _select("app/models/note.py") == [*ALWAYS, *MIGRATION_GUARDS]


def test_a_change_to_the_harness_runs_everything():
    for path in (
        "tests/conftest.py",
        "tests/api/conftest.py",
        "tests/databases.py",
        "tests/revisions.py",
        "requirements.txt",
        "requirements-dev.txt",
        ".github/workflows/ci.yml",
        "scripts/pr_tests.py",
    ):
        assert _select(path, "app/routers/notes.py") is None, path
