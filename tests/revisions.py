"""The Alembic chain as the tests see it: read from the script directory,
never from a revision id written into a test.

A revision's parent is the one fact most likely to change under a test without
the test noticing: fixing two heads reparents the newer revision (the
platform's `CLAUDE.md`, "Git Branches"), and a test that had the old parent
written in as a literal would then exercise the wrong step and stay green.
"""

import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def script_directory():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(ROOT / "alembic.ini"))
    # script_location is relative to the cwd, not to the ini file, so an
    # absolute ini path is not enough on its own. Same reason app/routers
    # /health.py overrides it.
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return ScriptDirectory.from_config(cfg)


def head_revision() -> str:
    """The chain's head, read from the revision files.

    Derived, never written as a literal: comparing against "0001_baseline"
    once meant the FIRST real migration would fail tests that had nothing to
    do with it.
    """
    heads = script_directory().get_heads()
    assert len(heads) == 1, f"expected one head, found {heads}"
    return heads[0]


def revision_before(revision: str) -> str:
    """The revision `revision` is built on - where a test stands to exercise
    `revision`'s upgrade, or lands after reversing it."""
    down = script_directory().get_revision(revision).down_revision
    assert isinstance(down, str), f"{revision} has no single parent: {down!r}"
    return down


def run_alembic(database_url: str, *args: str) -> subprocess.CompletedProcess:
    """Alembic as a SUBPROCESS, pointed at one database.

    `alembic/env.py` reads `app.config.settings` at import, which an already
    running test process cannot re-point; DATABASE_URL in the child's
    environment wins over everything else (app/config.py). A subprocess is also
    what a human runs.
    """
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT,
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
    )
