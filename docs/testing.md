# Testing

Last verified: 2026-11-18

**What this is for.** Which databases the tests build, how the migration tests
are kept honest, what CI runs on a pull request, and when it runs nothing.

## One database per run

Every database a test touches is created by `tests/databases.py` under a name
no other run can hold, `art_test_<epoch>_<hex>`, and dropped `WITH (FORCE)`
when its user is done with it. There is no fixed `art_test`, and no name is
read from `.env`: the server and credentials are the app's own settings with
only the database name swapped. Two runs - two worktrees, two sessions, CI
beside a laptop - therefore never build into the same database.

- **The run's database** is `test_engine` in `tests/api/conftest.py`: created
  once per session, built with `Base.metadata.create_all`, dropped when the
  session ends.
- **Scratch databases** are `scratch_database` in `tests/conftest.py`: one
  empty database per test, for the migration tests that build the chain
  themselves. Same helper, same prefix, same drop.
- **Leftovers.** The first fixture in a run that creates a database
  (`test_databases`, session-scoped) drops every `art_test_*` database that
  has no connections and is more than two hours old, so a crashed or
  interrupted run leaves nothing behind for long. One with a connection, or a
  younger one, belongs to a run in progress and is left alone - the age is
  what protects a run that has created its database and not yet connected.

`tests/unit/test_database_names.py` pins the names and the refusal to drop
anything else; `tests/api/test_run_databases.py` pins the leftover rule against
a real server, each refusal beside its mirror.

No test writes outside `tmp_path` and none creates a cluster-wide object (a
role, a tablespace, a database with a fixed name). The machine-wide pytest
lock in the platform's `CLAUDE.md` still applies until every app meets the
same rule; see the platform's `docs/registry.md`, "How an app's tests use the
shared server".

## Migration tests

`tests/test_migrations_build_the_schema.py` holds the generic guards - the
chain builds from zero, the result matches the models, there is exactly one
head - and the revision-specific tests, each of which exercises what one
revision does to existing data. `tests/test_migration_round_trip.py` holds the
release round trip.

**A test finds the revision below the one it exercises through Alembic's
script directory** (`tests/revisions.py`: `revision_before`, `head_revision`),
never by writing a parent's id in. Reparenting a revision to fix two heads
changes its parent, and a literal would then exercise the wrong step and stay
green.

**The round trip covers the release.** It upgrades a scratch database to head,
downgrades to the revision `origin/main` is at, upgrades again, and compares
every table, column, constraint and index with what it started from. The
revision on `origin/main` is found by its file: `git ls-tree origin/main
alembic/versions/` names the revision files main holds, and the walk down from
head stops at the first revision whose file is among them. When the branch
holds no revision beyond main, the range is one step (`-1`); when
`origin/main` cannot be read - a clone that has never fetched it - it falls
back to one step as well and says so with a warning (`git fetch origin` fixes
it). CI checks out the whole history, which brings `origin/main`.

## A refusal test needs something to refuse

`tests/unit/test_spa_routing.py` asserts both halves of the catch-all's
confinement: a real file in the bundle is served as itself, and a traversal
path (`/..%2F.env` and its spellings) is not. **The `.env` file the traversal
test writes beside the bundle is load-bearing**: `is_file()` is False for a
path that does not exist, so without a real file to leak the test would pass
against an unguarded handler. The first half is the mirror case, proving the
same handler does serve files and that the refusal is the guard's doing.

## What CI runs

`.github/workflows/ci.yml` (workflow name `Tests`) runs on every pull request
and on every merge-queue run (`merge_group`), and on nothing else, on
`ubuntu-latest`. Its one job is `test`, the check the repository rulesets
require on `main` and `dev`; it stays one job whatever the trigger, and its
steps are conditioned instead. It checks out the whole history, decides
whether the change touches anything but documentation, and then which backend
tests this run owes:

| trigger | backend tests |
| --- | --- |
| pull request into `dev` | `tests/unit`, plus every test file the pull request adds or edits |
| ...that touches `alembic/`, `alembic.ini` or `app/models/` | the above, plus `tests/test_migrations_build_the_schema.py`, `tests/test_migration_round_trip.py` and any other test file naming a revision the pull request adds or edits |
| ...that touches the test harness, the dependencies or the workflow | the full suite |
| `merge_group` (the merge queue into `dev`) | the full suite |
| pull request into `main` (the release), or any other base | the full suite |

On a pull request into `dev` the selection is `scripts/pr_tests.py <base>
<head>`, which prints the pytest arguments one per line, or `FULL`. Its
decision is a pure function, `select`, pinned by
`tests/unit/test_pr_tests.py`; it follows the shape of `media`'s and
`food`'s. A deleted test file is not selected, and a changed file under
`tests/unit/` is already covered by the unit tier.

"The test harness" is `tests/conftest.py`, `tests/api/conftest.py`,
`tests/databases.py`, `tests/revisions.py` and `scripts/pr_tests.py`; with
`requirements*.txt` and `ci.yml` itself, a change there changes what every
test means, so nothing is skipped. The revision-specific migration tests live
beside the generic guards in `test_migrations_build_the_schema.py`, so a
schema change runs the tests of the revision it adds along with every other
one.

Every other step runs on every non-documentation run, whatever the trigger:
`deploy/migrations` executable in the commit, exactly one Alembic head
(`alembic heads`, which reads the revision files and needs no database),
`ruff check .`, shellcheck, then `npm ci`, the frontend lint, the frontend
tests and the frontend build. Backend tests run with `-p no:cacheprovider`.

The `pull_request` run of a pull request into `dev` is the fast feedback; the
merge-queue run, on `dev` plus every pull request queued ahead of it, is where
the full suite runs before anything lands. That split is only sound while
`dev` merges through the queue (the platform's `docs/registry.md`, "What runs
when"). In a merge-queue run the diff's base and head come from the merge
group, since there is no pull request payload.

### Unit tests and database tests

The split is by directory:

- **`tests/unit/`** needs no PostgreSQL. Nothing in it requests a fixture that
  creates a database, and it passes with `DATABASE_URL` pointed at a port
  nothing listens on.
- **`tests/api/`** and the two migration files at the top of `tests/` need
  PostgreSQL: the API tests through `test_engine`, the migration tests through
  `scratch_database`.

A new test goes in `tests/unit/` exactly when it needs no database.

### A documentation-only pull request skips the job

The job's first step after the checkout diffs the pull request against its base
(`git diff --name-only <base>...<head>`, with the checkout at `fetch-depth: 0`
so the base is present). When every changed path is under `docs/` or ends in
`.md` — `README.md` and `CLAUDE.md` included, wherever they sit — every other
step is skipped, and `test` reports passed within seconds. One changed file of
any other kind runs the whole job, and so does an empty diff: the fast path is
taken only on positive evidence that nothing but documentation moved.

The run's log says which way it went: the deciding step prints every changed
path, and on the fast path its last line is `Documentation only: every other
step is skipped.`, with each later step marked skipped.

**It is a step condition, not a workflow-level `paths-ignore`.** A workflow
that does not run reports nothing, and a required check that is never reported
leaves the pull request blocked for ever. Skipping the steps inside a job that
does run reports `test` as passed, which is what the ruleset waits for.

The `postgres:17` service still starts, because a service cannot depend on a
step's output; that is most of the few seconds a documentation-only run takes.
Nothing in the suites reads a file under `docs/` or a Markdown file, which is
what makes skipping them sound — a test that starts to would have to be
covered by narrowing the rule.
