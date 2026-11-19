# The stack is the media tracker's: FastAPI, PostgreSQL, React + Vite, Alembic

art runs the same stack as `media`, so its patterns can be copied rather than
reinvented, and the platform's app contract is enforced by `apps.yml` and the
deploy pipeline rather than by every app being different.

**The stopwatch is the one feature on the box that genuinely wants a real
frontend.** It is live session state rather than a catalogue with notes, so
the SPA is better justified here than in any other app.

The accepted cost: a build step, a second port in development, and a
`frontend_dist/` that goes stale when nobody rebuilds.

Rejected: Django, and a server-rendered frontend.
