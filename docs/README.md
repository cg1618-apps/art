# Documentation for art

Start here. Every page describes the system **as it is**, in the present tense —
never how it got here. The record of how things changed lives in git history and
in `notes/`.

| Page | What it holds |
| --- | --- |
| `api.md` | Every endpoint: paths, bodies, the error shape, what search matches. |
| `data-model.md` | Every table and constraint, and what cascades. |
| `deployment-selfhost.md` | What a release does to the box, and what your options are when one fails. `bin/rollback` names this page when it freezes. |
| `frontend.md` | The frontend's layout and pages, and how the built bundle reaches a browser. |
| `logging.md` | What a log line looks like, why uvicorn's loggers are taken over, and why an inbound `X-Request-ID` is validated even though this app is gated. art's half of a platform contract. |
| `options.md` | Every vocabulary: the closed ones in code, the categories, and the seeded system options. |
| `notes/decisions.md` | Why things are the way they are, including rejected alternatives. The one place that is allowed to talk about the past. |
| `superpowers/specs/` | Working scaffolding for a task in progress. **Deleted when that task ends**, with anything durable moved into a real page first. |

Pages appear as the application does. The skeleton itself — ports, commands,
migration rules — is documented in `CLAUDE.md`.
