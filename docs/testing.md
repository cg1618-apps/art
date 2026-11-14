# Testing

Last verified: 2026-11-14

**What this is for.** What CI runs on a pull request, and when it runs nothing.

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
