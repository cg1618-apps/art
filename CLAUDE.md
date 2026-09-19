# CLAUDE.md — art

**The generic rules are not in this file.** Git workflow, branch and pull
request discipline, concurrent sessions, the machine-wide test lock, the
credentials rule, worktrees and documentation discipline live in
`cg1618-apps/platform`'s `CLAUDE.md`, one directory up. Claude Code loads it
first and this file second, so everything there applies here unless this says
otherwise.

## What this application is

**art** is a practice log and a reference shelf. What it is meant to hold, in
the owner's words:

- **progress and records**, and notes against them;
- a **record helper** — a stopwatch and timer for practice sessions;
- **what to draw**, **references**, and a **schedule**;
- **practices**, and **notes on tools**;
- **libraries** — expressions, accessories, and the like;
- a **roadmap**, and a library of **artists** worth following.

**The stopwatch is the outlier across all four applications.** Everything else
on this box is a catalogue with notes; a timer is live session state, and it is
the one feature that might reasonably want a different shape from the rest. It
is worth deciding this app's stack with that in mind rather than inheriting the
media tracker's by default.

## Status

**The skeleton is built; no feature is.** FastAPI serves `/health` and the
built SPA, Alembic's chain holds one empty baseline revision, and the deploy
pipeline's hook, the production compose file and both workflows are in place.
There is no schema and no module from the table in `docs/notes/decisions.md`.

Each module gets its own design pass immediately before it is built —
brainstorm into `docs/superpowers/specs/`, then plan, then implement.

## The contract this app owes the platform

Four things, none of which names a framework:

1. **A container listening on port 8003**, publishing nothing to the host.
2. **A health path** that answers 200 only when the app can actually serve —
   not a route that returns 200 with the database down. It is declared in the
   platform's `apps.yml` as `/health`; change it there if this app exposes
   something else.
3. **`DATABASE_URL` read from the environment.**
4. **A `main` branch that is production**, moving only by pull request.

The platform's `docs/registry.md` and `docs/shared-stack.md` hold the detail,
including the network alias (`art-app`) the tunnel routes to.

## Stack

**FastAPI + PostgreSQL on the backend, React + Vite on the frontend** — the
same shape as the media tracker, deliberately. Four months of patterns exist to
copy from, and the platform's app contract is enforced by `apps.yml` and the
deploy pipeline rather than by every app being different.

The cost is known and accepted: a build step, a second port in development, and
a `frontend_dist/` that goes stale if you forget to rebuild. The media
tracker's `CLAUDE.md` documents each of those.

Migrations: Alembic. This app ships `deploy/migrations` with `current`,
`added` and `downgrade` — the hook the platform's rollback calls. See
"Migrations" below.

## Who can see it

**Nobody but you, today.** `exposure: cloudflare-access` in the platform's
registry: Cloudflare authenticates before a request reaches the box, so there
is no login page, no session, no password and no auth code in this app. One
user, one person's data.

**But publishing is expected** — finished work, and possibly notes worth
sharing. That is why this app is *not* on the platform's never-public list: for
`journal`, `health` and `money` public is never correct; here it is a change the
app is meant to want.

Three things make that change cheap, and all three are free now and expensive
later:

1. **Anything shareable lives under `/s/...`** from the first route. Publishing
   one piece is then an Access policy that exempts that prefix, not a redesign —
   because Access is all-or-nothing per path.
2. **Shareable entities carry a visibility field from the first migration** —
   `private` / `unlisted` / `public`, everything `private`. The column is
   trivial to add later; retrofitting the *checks* at every read path is not.
   Note that this cuts across the app: a piece may be public while the practice
   notes attached to it are not.
3. **A password on a shared thing is a share token, not an account.** There is
   never a second identity here, so the model is "this piece has a secret link,
   optionally with a passphrase" — a field on the object, never a users table.

**The dangerous moment is the flip**, if it ever comes: moving from
`cloudflare-access` to `public` moves the gate from Cloudflare into this
codebase. The visibility checks have to work *before* that lands, and be tested
for refusal with fixtures that make refusal possible — a check over an empty set
passes without ever firing.

## Ports

Both come from `apps.yml`, and both are box-wide: all four apps may run on one
laptop at once, so neither may be changed to dodge a collision.

- **8003** — uvicorn. The registry port, the `PORT` the production container is
  given, and the port the `art-app` network alias is routed to.
- **5176** — the Vite dev server, `5173 + (8003 - 8000)`, with `strictPort` so
  a taken port aborts rather than silently moving.

Vite proxies **both** `/api` and `/health` to 8003. This app's health path is
`/health`, not `/api/health` — `apps.yml` declares it and the deploy pipeline
waits on it — so `app/main.py`'s SPA catch-all refuses anything under `health/`
as well as under `api/`. Without that a mistyped probe is answered by the
bundle with a 200, and a health check that cannot fail is worse than none.

## Commands

```bash
.\dev.ps1                                  # postgres + uvicorn + vite
venv/Scripts/python.exe -m pytest -q       # tests
venv/Scripts/ruff.exe check .              # lint
venv/Scripts/python.exe -m alembic upgrade head
cd frontend && npm run build               # writes frontend_dist/ for uvicorn
cd frontend && npm run lint                # oxlint
```

**After any frontend change run `npm run build`**: uvicorn on 8003 serves the
prebuilt bundle in `frontend_dist/`, which the Vite dev server on 5176 does not
use. A change that appears on one port only is a stale build.

`frontend_dist/` is gitignored and rebuilt per machine, as are `venv/` and
`node_modules/`.

## Migrations

Alembic, single head. The chain starts at `0001_baseline`, which is
deliberately empty: it exists so `tests/test_migrations_build_the_schema.py`
can prove from the first commit that the chain builds against a scratch
database from zero, rather than from whenever someone remembers to add it.

```bash
venv/Scripts/python.exe -m alembic heads     # more than one line = broken
venv/Scripts/python.exe -m alembic revision --autogenerate -m "describe change"
```

`deploy/migrations` is the hook the platform's rollback calls — `current`,
`added`, `downgrade`. It **must** be mode `100755` in the commit; verify with
`git ls-tree HEAD -- deploy/migrations`, never `git ls-files`, which reads the
index and has given false passes. Fix a wrong mode with
`git update-index --chmod=+x deploy/migrations`.
