# art

Practice records, references, schedule, and the drawing roadmap.

One of the applications on the [cg1618 platform](https://github.com/cg1618-apps/platform).
It is registered in that repository's `apps.yml`, which assigns it
`art.cg1618.com`, port 8003 and the database `art`.

FastAPI serves the API, `/health` and a React bundle. The schema is built by
Alembic, from an empty `0001_baseline` through revisions that add notes and
options, the roadmap, exercises, drills and practice records, the timer, and
references. What a rollback does to that data is in
[`docs/deployment-selfhost.md`](docs/deployment-selfhost.md).

`main` is production and moves only by a release pull request from `dev`.
