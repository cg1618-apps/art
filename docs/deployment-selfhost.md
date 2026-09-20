# Deployment, and getting back from a bad one

Last verified: 2026-09-20

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

### For `art`, today, reversing the schema destroys nothing

This is the one place this page differs from `travel`'s and `food`'s, and it
will not stay true.

`art` has exactly one revision — **`0001_baseline`** — and its `upgrade()` is
deliberately empty. It creates no tables. There is nothing for a downgrade to
drop, and no rollback of this app can currently lose a row, because there are
no rows.

So if a release of `art` fails today, **roll back freely**. The decision that
costs something in the other apps costs nothing here.

### What changes the moment that stops being true

The first revision that creates a table makes this page's most important
section wrong, and nothing will announce it. Whoever writes that revision
**updates this section in the same commit**, with:

- the revision id, named;
- the tables it creates, named;
- one sentence saying that downgrading past it drops them and everything in
  them.

`travel/docs/deployment-selfhost.md` is the worked example — its
`p1acking0001` section says exactly that about `packing_list`, `packing_item`
and `label_option`. Copy its shape.

### The dump is not a gentler path, and that trap arrives with the first table

Worth knowing before it applies, because the reasoning is not obvious and the
moment to learn it is not mid-incident.

The pre-deploy dump is taken **before** the release, so restoring it discards
everything written since. `bin/rollback` refuses to do that automatically for
exactly that reason: it would throw away every write since the dump to recover
from a failure that usually did not touch data at all. So it freezes, names the
dump, and stops.

Once this app has tables, there will be **no route that keeps the data**. The
real choice becomes: roll back and lose everything entered since the release,
or fix forward with a corrected build. For data entered by hand — which
practice records and references are — fix forward is usually right, and rolling
back is usually only right when the app cannot serve at all.

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
`docs/deployment-selfhost.md`. This app has one revision and one hook; a second
page would be a second place to go stale. If `deploy/` grows past the single
hook, split it then.
