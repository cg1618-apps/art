# Documentation for art

Start here. Every page describes the system **as it is**, in the present tense —
never how it got here. The record of how things changed lives in git history and
in `notes/`.

| Page | What it holds |
| --- | --- |
| `deployment-selfhost.md` | What a release does to the box, and what your options are when one fails. `bin/rollback` names this page when it freezes. |
| `logging.md` | What a log line looks like, why uvicorn's loggers are taken over, and why an inbound `X-Request-ID` is validated even though this app is gated. art's half of a platform contract. |
| `notes/decisions.md` | Why things are the way they are, including rejected alternatives. The one place that is allowed to talk about the past. |
| `superpowers/specs/` | Working scaffolding for a task in progress. **Deleted when that task ends**, with anything durable moved into a real page first. |

There is little else yet: the skeleton is built but no module is, so there is
no schema to describe and a single endpoint. `deployment-selfhost.md` and
`logging.md` are here early on
purpose - it describes a contract every app on the box shares, and the moment
to adopt it is while there are no log calls to convert rather than after there
are. Pages appear as the
application does — a data model page when there is a schema, an API page when
there are endpoints. The skeleton itself is documented in `CLAUDE.md`, which is
where its ports, commands and migration rules live.
