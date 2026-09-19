# art

Practice records, references, schedule, and the drawing roadmap.

One of the applications on the [cg1618 platform](https://github.com/cg1618-apps/platform).
It is registered in that repository's `apps.yml`, which assigns it
`art.cg1618.com`, port 8003 and the database `art`.

**The skeleton is built; no feature is.** FastAPI serves `/health` and a React
bundle, Alembic holds one empty baseline revision, and the deploy pipeline's
hook and workflows are in place. There is no schema yet.

`main` is production and moves only by a release pull request from `dev`.
