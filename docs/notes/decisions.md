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

## The catch-all serves real files, the way `media` does

The SPA catch-all inherited from travel's skeleton answered **every** non-API
path with `index.html`. That is correct for a client route and wrong for a file
that actually exists in the bundle: `/favicon.svg` came back as the SPA's HTML
under `text/html`, and the browser discarded it. Only `/assets` was mounted as
`StaticFiles`, and Vite copies `frontend/public/` to the **root** of the bundle,
not into `assets/` — so nothing served it. Nothing sits in front of this app
either; cloudflared connects straight to uvicorn, so there was no proxy to cover
the gap. The icon shipped in the repository and had never been served.

**The fix is `media`'s resolve-and-confine block, adopted rather than
redesigned**, per the platform's house-style rule that `media` is where a
convention is looked up. The handler resolves `dist / full_path`, and serves it
only when it is inside the dist directory, is not the directory itself, and is a
real file; otherwise it falls back to `index.html`. This is art conforming to
the platform, not one of this app's deliberate divergences — the stopwatch is
where those are expected, and nothing about serving an icon is particular to
art.

The `api` and `health` prefix guards keep their place in front of it, and keep
their loop: this app's health path is `/health`, so a mistyped probe must still
404 rather than answer 200 with the bundle.

Rejected: **special-casing the icon paths** — a list of `/favicon.svg`,
`/favicon.ico`, `/robots.txt` and whatever comes next. It is shorter today and
it is a list somebody has to remember to extend, with the same silent failure
each time a file is added to `frontend/public/`. Rejected: **mounting the whole
dist as `StaticFiles` with `html=True`**, which would serve the files but hand
the client-route fallback to Starlette, and with it the `/api` and `/health`
404 guards this app cannot give up.

**The `.resolve()` + `is_relative_to()` + `is_file()` guard is load-bearing
security, not tidiness.** `full_path` is user-controlled, and without the
confinement `/..%2F.env` reads the app's own credentials from beside the bundle.
`tests/test_spa_routing.py` asserts both halves — that a real file in the bundle
is served as itself, and that a traversal attempt is not — and the `.env` file
its traversal test writes is load-bearing: `is_file()` is False for a path that
does not exist, so without a real secret to leak the test would pass against an
unguarded handler.

## Structure

Eleven modules, built in this order. Each gets its own design pass
immediately before it is built, not now. Modules 1 to 8 are the first build
block; the rest wait until it is done.

| | Module | Owns | Depends on |
| --- | --- | --- | --- |
| 1 | Notes + Options | knowledge not tied to one thing (terms, tips, advice); the open vocabularies every module reads | — |
| 2 | Goals | the levels: L0 Foundations, L1 Figure, L2 Character, L3 Scene, L4 Colour, L5 Illustration | — |
| 3 | Roadmap | the stages of each level, and the test that closes each | 2 |
| 4 | Schedule | when to practise what | 3 |
| 5 | Record + Exercise | exercises (練習項目) and drills (練法); what was practised, when, for how long | 3 |
| 6 | Timer | stopwatch and countdown; produces a record | 5 |
| 7 | Tool | notes on materials and software | — |
| 8 | Reference | reference images and links, tagged | — |
| 9 | Plan to draw | what to draw next | 8 |
| 10 | Artist | who is worth following, links, what to take from them | — |
| 11 | Works | finished pieces, with images | 5 |

Roadmap, Schedule, Record + Exercise and Timer matter most. The order changed
once, before anything was built: Records was first, and Notes + Options went
ahead of it because every later module reads system options, and the page that
manages them costs little more alongside the first module that uses them.
Goals and Roadmap went ahead of Records because how to record and what an
exercise is cannot be decided before what the practice is for.

### Entities

As agreed before any of them was designed in detail; each module's design pass
settles the rest.

- **Note** — built; see `docs/data-model.md`.
- **Exercise** (練習項目) and **Drill** (練法) — `food`'s dish and recipe. An
  exercise is what is practised (gesture drawing, box in perspective) and sits
  on a roadmap stage; a drill is one prescribed way of doing it (Line of
  Action 30s × 20), with its source, source links, resources, instructions,
  unit, target, suggested minutes and frequency. Both carry a remark and
  name–link resources.
- **Record** — one record per exercise practised: date, location, an optional
  duration in minutes, a drill **or** an exercise **or** neither (never both:
  the exercise is read through the drill), a `kind` (practice, piece, test), a
  method, a tool, name–link reference links, notes. Images are designed later
  (Google Drive or Google Photos).
- **Work** — names, images, status, and the `visibility` field every shareable
  entity here carries.
- **Reference** — an image or a link, plus tags.
- **Artist** — names, links, notes on what is worth learning from them.

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
  near-identical screens to build and maintain. Tags are system options, so a
  library is one option category.
- **Works come last, and sharing comes with them.** Nothing is shareable until
  there are finished pieces to share, so the `/s/...` prefix and the
  `visibility` field stay reserved and unused until Works. `note` already
carries the field, from its first migration, for the same reason. They are still
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

`name_cn`, `name_en` and `name_alt`, at least one required, with `name_cn` as
the display default, and the aliases in a child table that is searched and
never displayed — `food`'s dish shape, which `note` follows exactly.

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

## Options follow `media`'s tiers, with four divergences

Tags and every other open vocabulary are `system_option` rows, `media`'s Tier
2, decided by `media`'s question: does code branch on the exact value? The
lighter alternative, `travel`'s `label_option` (suggested values stored as
text), was rejected because a rename there has to rewrite every row that
copied the text, and the owner asked for system options by name.

Where art departs from `media`, deliberately:

- **Integer ids**, not a UUID `system_id`. art's skeleton is `travel`'s, and
  every table in `travel` and `food` uses integers.
- **`description` beside `remark`.** `media`'s `remark` is an admin note shown
  read-only on one page. A description is written for the moment a value is
  picked, and every picker shows it: two audiences, two columns.
- **Categories are registered in code** (`OPTION_CATEGORIES`), not free text on
  the API. Every category is read by some field, so an unregistered one is a
  typo, and each needs a label and a description of its own for the Options
  page.
- **A delete in use states its cost and is checked.** `media` deletes silently
  and cascades the tags away. Here the page shows the count, the request
  echoes it, and a stale count is a 409 - `food`'s `StaleCountError`.

No scope, usage or alias tables: they answer questions `media` has (which media
type, which source field, which external API string) that art does not.

## Notes are one table, filed by an option

Terms, knowledge, tips and advice are one `note` table with a `note_category`
option, not four tables or a code enum: nothing behaves differently for a 名詞
than for a 小技巧, so the category files a note and nothing more, and a new
category is a row. The glossary is Notes filtered to 名詞. A note's `summary`
is its definition when it is a term.

Search covers names, aliases and the summary, and not the body: a word inside
a long note would bury the note you meant.

Notes about one tool belong to the Tool module and a record's notes to the
record; Notes holds what is tied to neither.

## The frontend foundation is `food`'s

There was no frontend before this module, so one had to be chosen. It is
`food`'s: one `client.js` that calls `fetch`, `endpoints.js`, `useApiQuery` /
`useApiMutation` over TanStack Query, `useUrlFilters`, react-router 7,
Tailwind 4 with `food`'s tokens, Vitest. `media`'s Options page uses raw
`fetch` in `useEffect` and react-router 6, the older shape of the same ideas.

Markdown is `media`'s `ResourceMarkdown` configuration, because `food` has no
renderer: `react-markdown` and `remark-gfm`, no raw HTML, `javascript:` links
inert.

## Goals are levels, and every level and stage ends in a test

The roadmap was agreed with the owner before the module was designed, and the
migration seeds it. Its shape:

- **Levels are named for what you can draw** — 基礎, 人體, 角色, 場景, 上色,
  插畫 — not short / mid / long term. At ten minutes a day nobody can promise a
  duration; a level is passed by its test, never by a date. The owner first
  had four goals; splitting "short term" into the figure and the finished
  character, and adding a foundations level below it, made six.
- **Every level and stage carries a test**: a piece redrawn over time, which
  gives progress a picture rather than only hours. Records attach to those
  tests in the Record module.
- **The order follows what the owner values**: perspective and proportion
  before detail, "rough but good" over "it looks weird". The figure in
  perspective (stage 5) is the stage that fixes "it looks weird"; muscle
  anatomy comes after gesture and stays at the level of masses; composition
  waits for the scene level, since a lone character needs little of it. Line
  drills shrink to a warm-up rather than a stage of months.
- **Status is set by hand**, not derived from the stages, so a level can be
  passed on its test before every stage is ticked.
- **The stage number is derived** from the order, so reordering never leaves a
  stale number behind.
- **A goal with stages is RESTRICT, not CASCADE**: the stages are the roadmap,
  and deleting a level header is the wrong way to lose them.

Goals and Roadmap are two modules in "Structure" and were built as one: a level
is nothing without its stages, and neither page is useful alone.

## Records, exercises and drills

Agreed with the owner before the design, and built as agreed:

- **An exercise is `food`'s dish and a drill its recipe.** The exercise is what
  is practised and sits on a stage; a drill is one prescribed way of doing it,
  from a course or the owner's own notes. "Exercise type" was the working name
  for the general thing until the owner found it awkward.
- **One record per exercise practised.** A ten-minute session of warm-up then
  stage work is two records, because progress is read per exercise.
- **A record names a drill, an exercise, or neither, never both**, so the two
  cannot disagree: through a drill the exercise is derived. `food`'s recipe
  lines name an ingredient or a dish on the same reasoning.
- **A test record names exactly one stage or one level.** The database holds it
  as `num_nonnulls(stage_id, goal_id) = CASE WHEN kind = 'test' THEN 1 ELSE 0
  END`; the first draft, `(kind = 'test') = (count = 1)`, would have let a
  practice record carry both.
- **Records RESTRICT what they name.** A record is history; a deleted drill
  that silently orphaned a month of records would be the worst kind of loss.
- **Location was kept** from the owner's old spreadsheet; "finished one unit"
  and a "what looked weird" tag were proposed and declined. The old log was not
  migrated.
- **No visibility on exercises or records.** They are the practice log, never
  shared; a finished piece is shared as a Work, which carries the field when
  that module is built.
- **The seed comes from what the owner already has**: their 細節指示 and the
  assignments of the three Udemy courses they finished without practising. The
  courses' own frequency wording is kept as written rather than normalised.
- Images are deliberately absent: the owner will keep them in Google Drive or
  Google Photos, and that is designed on its own.
