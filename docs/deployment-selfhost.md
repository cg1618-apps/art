# Deployment, and getting back from a bad one

Last verified: 2026-11-19

**What this is for.** What a release of `art` does to the box, and what your
options are when one fails. `bin/rollback` names this page when it freezes —
its last line is *"restoring it is a human's decision; see the app's deploy
notes"* — so it is written to be read under pressure: **the section that
matters is [When the rollback freezes](#when-the-rollback-freezes)** and it is
near the top for that reason.

The platform owns the pipeline and documents it in `cg1618-apps/platform`
(`docs/registry.md`, `docs/shared-stack.md`). This page holds only what is
specific to this app.

## What a release does

`main` moves by pull request, the reusable workflow builds the image, and
`bin/deploy` puts it on the box. Two things then happen that matter here:

1. **`entrypoint.sh` runs `alembic upgrade head` on every container start.**
   The schema is brought up by the app itself, not by a separate step.
2. **`/health` answers 200 only when the revision the database is stamped with
   matches the head the running image ships.** A half-applied deploy fails this
   even though pages still serve, which is the whole point of it.

   `/health`, not `/api/health` — `apps.yml` declares it and the deploy
   pipeline reads the probe's path from there. The two must agree or the
   pipeline probes a path this app does not serve.

**A release that adds or modifies a revision under `alembic/versions/` waits
for the owner after the merge.** The platform's workflow sends it down the
gated lane, which holds the deploy until it is approved in this repository's
`production` environment; any other release deploys unattended.
`./deploy/migrations added origin/main origin/dev` answers which lane a
release will take before it is opened — any output means gated — and the
release PR says so when its text is proposed and again when it is opened (the
platform's `CLAUDE.md`, "Git Branches").

`deploy/migrations` is the hook the platform calls. It has three subcommands —
`current`, `added` and `downgrade` — and it must be committed executable
(`git ls-tree HEAD -- deploy/migrations` must show `100755`; CI asserts it).

## When the rollback freezes

`bin/rollback` exits **3** and stops. It has already told you the pre-deploy
dump, the git revision the code was at, and the revision the schema was at.

**Read this before restoring anything.**

### `bin/rollback` never restores data

It reverses *schema*, through this app's own migration hook, and swaps the
image back. That is deliberate and it is in the script's own header: undoing a
dropped table recreates it **empty**, so a migration that dropped data leaves
that data only in the dump.

### For `art`, reversing the schema destroys data

`bin/rollback` reverses only the revisions **the failed release added**. It
downgrades to the revision `bin/deploy` read from the database before the pull
(the dump's `.migration` file), with `alembic downgrade <target>` run from the
new image. A release that added no revision file gets no downgrade at all —
only the image swap. Reversing a revision an *earlier* release shipped is
never automatic; it is a hand-run `./deploy/migrations downgrade <target>`,
and costs the same as the table below.

Every revision after `0001_baseline` creates or reshapes something, and
downgrading past it loses what its `downgrade()` drops. In chain order:

| Revision | Downgrading past it loses |
| --- | --- |
| `0001_baseline` | Nothing. Its `upgrade()` and `downgrade()` are both deliberately empty. |
| `0002_notes_and_options` | `system_option`, `note`, `note_alias`, `note_resource` and `note_topic` — every note, and every option in every category, seeded or added. |
| `0003_goals_and_roadmap` | `goal`, `stage` and `stage_resource` — the whole roadmap, including every edit made to the seeded levels and stages. |
| `0004_exercises_and_records` | `exercise`, `exercise_alias`, `exercise_resource`, `exercise_topic`, `drill`, `drill_source_link`, `drill_resource`, `record` and `record_reference` — **every practice record**, every exercise and drill, and every `source`, `location` and `tool` option. |
| `0005_timer` | `active_timer` — a timer running at the time is lost. A timer is not history, so nothing else is. |
| `0006_timer_draft` | `active_timer.draft` — the record a running timer was filling in. |
| `0007_note_name` | Each note's single `name` goes back into `name_cn`; `name_en`, `name_alt` and `note_alias` come back **empty**. No typed text is lost: the other names stay in the note's remark as the `其他名稱：` line the upgrade wrote, which the downgrade does not take back out. |
| `0008_references` | `reference` and `reference_group` — every reference and its group tags, and every `reference_group` option. |

Upgrading again recreates a dropped table, not what was in it: `0002`, `0003`
and `0004` re-seed their starting rows on the way back up, but none of the
owner's edits or entries.

**No revision declares itself irreversible.** None carries a marker, and
`deploy/migrations downgrade` checks for none: it hands the target straight to
Alembic. The platform's contract (`docs/registry.md`, "the hook answers three
subcommands") requires the hook to refuse a revision whose author declared it
irreversible; this hook meets that only vacuously, because there is nothing to
refuse. The first revision whose downgrade would invent data rather than
reverse a shape needs a marker and a hook that greps for it — `media`'s
`irreversible = True` is the convention to copy.

### The pre-deploy dump is the way back, and it is not a gentler path

A downgrade's losses are recoverable **only from the pre-deploy dump** —
nothing else holds them. But the dump is taken **before** the release, so
restoring it discards everything written since. `bin/rollback` refuses to do
that automatically for exactly that reason: it would throw away every write
since the dump to recover from a failure that usually did not touch data at
all. So it never restores: when it cannot go on safely it freezes, names the
dump and stops, and when it does finish a downgrade it ends with *"SCHEMA was
reversed. DATA was NOT restored"* and names the dump again.

| Option | What it costs |
| --- | --- |
| Let `bin/rollback` downgrade | Whatever the table above says for every revision the release added. |
| Restore the pre-deploy dump | Every write made since the release. |
| Fix forward | Nothing, if you can ship a fix. |

**There is no route that keeps the data.** For data entered by hand — which
practice records, notes and references are — fix forward is usually right, and
rolling back is usually only right when the app cannot serve at all and a fix
is not minutes away.

Ask the database what it is at before deciding ([What the database is
at](#what-the-database-is-at)): a downgrade costs the rows of every table above
from the revision after the target up to the one it reports. This page does
not record what production is at; only the box can say that.

### Where the dumps are

```
~/backups/art/pre-deploy-<timestamp>.dump
~/backups/art/pre-deploy-<timestamp>.dump.revision    # git revision of the code
~/backups/art/pre-deploy-<timestamp>.dump.migration   # revision the DB reported
```

Five are kept; the newest is the one the failing deploy took. The freeze
message prints the same paths, so what it names and what is listed here should
agree — **if they ever disagree, believe the box.**

## What the database is at

The revision the **database** is stamped with, read from the database rather
than from the image:

```bash
# on the box, straight from PostgreSQL
docker exec cg1618-db-1 psql -U postgres -d art -tAc \
  "SELECT version_num FROM alembic_version"

# or through this app's own hook, which is what bin/deploy and bin/rollback ask
cd ~/art && PLATFORM_DIR=~/cg1618 ./deploy/migrations current
```

An app whose schema has never been migrated has no `alembic_version` table at
all, and the hook's answer there is `base` rather than an error — that is this
app's first deploy, and a hook that failed instead would refuse the very deploy
that creates the schema.

## The shared database is shared

`art` has no database of its own on the box. It uses the platform's
PostgreSQL — one container, one database per app, in the `cg1618` compose
project.

**On the box, use `docker compose stop db`, never `docker compose down`.** A
`down` removes the container all four apps are using, and on the box that is
production's database taken out from under four apps with nobody in front of
it. `down` without `-v` leaves the named volume alone, so it is recoverable —
but it is an outage nobody asked for.

On a **development** machine this is no longer a trap. The development database
moved out of `media`'s compose project into the platform's own
(`docker-compose.dev-db.yml`, container `cg1618-dev-db`), so nothing an app
runs can adopt or destroy it. It used to be possible, and it happened on
2026-09-19.

## Why there is one page here and two in `media`

`media` splits this across `deploy/README.md` and
`docs/deployment-selfhost.md`. This app has one hook and no other deploy
tooling; a second page would be a second place to go stale. If `deploy/` grows past the single
hook, split it then.
