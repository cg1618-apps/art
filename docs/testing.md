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

## What CI runs

`.github/workflows/ci.yml` (workflow name `Tests`) runs on every pull request
and on nothing else, on `ubuntu-latest`. Its one job is `test`, the check the
repository ruleset requires on `main` and `dev`. It checks out the whole
history, decides whether the pull request changes anything but documentation,
and only if it does goes on to assert that `deploy/migrations` is executable in the commit, `ruff check .`, shellcheck, the pytest
suite against a `postgres:17` service, then `npm ci`, the frontend lint, the
frontend tests and the frontend build.

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
