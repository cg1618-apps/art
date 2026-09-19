# Decisions

Why art is the way it is. Unlike the rest of `docs/`, this page is allowed to
talk about the past: it records what was chosen, what was rejected, and the
reasoning that is still load-bearing.

## Platform decisions this app inherits

Recorded in `cg1618-apps/platform` rather than here, and summarised only so far
as they bind this app:

- **It is its own repository**, sharing no code with the other applications. The
  platform connects them by configuration, not by git pointers.
- **It shares one PostgreSQL**, with its own database and its own role.
- **It is `public`**, because repository rulesets and environments with required
  reviewers are free only for public repositories, and both gates depend on it.
- **No `pull_request`-triggered job may run on the self-hosted runner.**

## Decisions for this application

- **FastAPI, PostgreSQL, React + Vite, Alembic** — the media tracker's stack.
  Rejected: Django and a server-rendered frontend. **The stopwatch is the one
  feature on this box that genuinely wants a real frontend**, being live session
  state rather than a catalogue with notes, so the SPA choice is better
  justified here than anywhere else.
- **Cloudflare Access over the whole hostname, and no auth code in the app.**
  One user, no accounts. Rejected: an app-level password, for the same reasons
  as `travel`.
- **The skeleton is travel's, copied and renamed.** `travel` is the smallest
  app on the box and was already through a first deploy, so its shape — the
  `create_app(dist)` factory, the revision-comparing health probe, the
  `deploy/migrations` hook, the production compose file and the two workflows —
  is the one with the production failures already taken out of it. Rejected:
  starting from the media tracker, which carries four months of features this
  app has no use for, and starting from nothing.
- **The health path is `/health`, not `/api/health`.** `apps.yml` declares it,
  and the deploy pipeline reads the path it waits on from there, so the
  registry is the authority and the app follows it. The cost is that the SPA
  catch-all has to refuse `health/...` as well as `api/...`: a health path
  outside `/api` is otherwise answered by the bundle with a 200, and a probe
  that cannot fail is worse than no probe. The Vite dev proxy forwards both
  prefixes for the same reason.
- **Ports 8003 and 5176**, from `apps.yml` and from the box-wide rule
  `Vite = 5173 + (port - 8000)`. All four apps may run on one laptop at once,
  so a collision is resolved in the registry, never by a local edit —
  `strictPort` makes Vite abort rather than move.
- **Publishing is anticipated, not built.** `/s/...` for anything shareable, a
  `visibility` field from the first migration, share tokens rather than
  accounts. Note the cross-cutting case: a piece may be public while the
  practice notes attached to it stay private, so visibility belongs on the
  entity rather than on a section of the app.

## Structure

Eight modules, built in this order. Each gets its own design pass immediately
before it is built, not now.

| | Module | Owns | Depends on |
| --- | --- | --- | --- |
| 1 | Records | what was drawn or practised, when, for how long, notes | — |
| 2 | Timer | stopwatch and countdown; produces or updates a record | 1 |
| 3 | Artists | who is worth following, links, what to take from them | — |
| 4 | Tools | notes on materials and software | — |
| 5 | References | reference images and links, tagged | — |
| 6 | Roadmap | skills and targets, with status | 1 |
| 7 | Schedule | when to practise | 1 |
| 8 | Works | finished pieces, with images | 1 |

### Entities

- **Record** — date, a `kind` (practice, work, study), a **nullable** duration,
  notes, and an optional link to a work.
- **Work** — names, images, status, and the `visibility` field every shareable
  entity here carries.
- **Reference** — an image or a link, plus tags.
- **Artist** — names, links, notes on what is worth learning from them.
- **ToolNote**, **RoadmapItem**, **ScheduledPractice** — text, tags, status.

### The decisions behind that shape

- **The record is the spine, and the timer is optional.** The stopwatch is one
  way to produce a record, never the only way: duration is nullable, records
  can be written after the fact, and the app is fully usable by someone who
  never starts a timer. Building it the other way round — sessions created only
  by the recorder — would make the app useless on every day the recorder was
  not used, which is most of them.
- **This is the third time the same principle decided a model**, alongside
  `food`'s ingredient stubs and `travel`'s trip-less packing lists: **none of
  these applications may demand bookkeeping before it is useful.** Anything
  that requires a parent record, a timer or a setup step before the thing you
  actually want to do is a reason the app stops being opened.
- **Expressions and accessories are tags on references, not libraries of their
  own.** They are the same kind of thing, and three tables would mean three
  near-identical screens to build and maintain.
- **Works come last, and sharing comes with them.** Nothing is shareable until
  there are finished pieces to share, so the `/s/...` prefix and the
  `visibility` field stay reserved and unused until module 8. They are still
  designed in from the start, because retrofitting visibility checks across
  every read path is the expensive half.

### Image storage

References and works need uploaded images, and this app is not the only one —
`food` needs them too. That makes it a platform question rather than an
application one: a bind-mounted directory outside the container image, and
backup coverage, are both things the media tracker already has and the platform
has not yet generalised. Recorded in the platform's Step 4 plan; nothing here
should invent its own answer.

The constraint worth carrying: an uploaded image is the one kind of data that
cannot be re-fetched from anywhere. The media tracker distinguishes covers,
which the APIs can supply again, from `static/library`, which nothing can.

### Naming

`name_cn`, `name_en`, `aliases[]`, with `name_cn` as the display default — the
platform-wide convention, shared with `food` and `travel`.

### Out of scope, deliberately

Anything that analyses the images themselves. Time-tracking reports beyond
what a list of records shows. Anything multi-user beyond the eventual
read-only share of a finished piece.

## The rollback was rehearsed, and it worked

`downgrade` had never run end to end on any app in this platform. The refusal
path was tested against a scratch chain that never reverses anything; the
reversal itself had never executed. That made it the largest untested piece of
the system, and the one that runs unattended on the box a minute after a
failed deploy.

So a release was built to fail on purpose: a revision creating a table, and a
`/health` that answers 503 behind an environment variable set only in the
production compose. It was deployed to art, whose database is empty and which
nothing depends on.

Every step ran, in order and without help:

```
schema was at 0001_baseline
==> Tagging the outgoing image as art-app:previous
==> Waiting for health
art not healthy after 180s          -> exit 2
==> Deploy failed. Rolling back art toward c011f4e
==> This deploy added migrations:
==> Downgrading to 0001_baseline
==> Restoring the previous image
==> Re-checking health
healthy
```

The box was checked afterwards against the state recorded before: revision
back at `0001_baseline`, the table dropped, the checkout returned to the
pre-deploy revision, the container healthy on the previous image.

Three things worth keeping from it:

- **`exit 2` reaches the rollback, and `exit 1` must not.** The distinction is
  the pipeline's most expensive mistake and it is now observed rather than
  argued.
- **A rollback leaves the checkout detached** at the revision the dump belongs
  to. `bin/deploy` returns it to `main` on the next run, which is why that
  recovery exists: without it one rollback disables automatic deploys
  silently.
- **The image tag is load-bearing.** `art-app:previous` did not exist before
  this deploy — art had only ever had one — and the deploy created it by
  tagging the outgoing image. Had that step not run, the rollback would have
  frozen rather than swapped.

What this did **not** test is the refusal: a revision marked
`irreversible = True` must never be reversed, so it cannot be rehearsed by
reversing one. That stays covered by the hook's own tests. Nor did it test the
data restore, which is deliberately manual - `bin/rollback` reverses the
schema and says, in capitals, that the data was not restored.
