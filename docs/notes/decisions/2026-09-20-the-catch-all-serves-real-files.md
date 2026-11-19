# The SPA catch-all serves real files, the way `media` does

Vite copies `frontend/public/` to the **root** of the bundle, not into
`assets/`, and only `/assets` is mounted as `StaticFiles`. Nothing sits in
front of this app — cloudflared connects straight to uvicorn — so a catch-all
that answers every non-API path with `index.html` serves `/favicon.svg` as HTML
and the browser discards it. What the handler does now is in `frontend.md`,
"How the built bundle is served".

**The fix is `media`'s resolve-and-confine block, adopted rather than
redesigned**, because `media` is where a convention is looked up. This is art
conforming to the platform, not one of its deliberate divergences: nothing
about serving an icon is particular to art.

The `api` and `health` prefix guards stay in front of it: this app's health
path is `/health`, so a mistyped probe must still 404 rather than answer 200
with the bundle.

**The `.resolve()` + `is_relative_to()` + `is_file()` guard is security, not
tidiness.** `full_path` is user-controlled; without the confinement
`/..%2F.env` reads the app's own credentials from beside the bundle. How the
test proves it is in `testing.md`.

Rejected:

- **Special-casing the icon paths** — a list of `/favicon.svg`, `/favicon.ico`,
  `/robots.txt` and whatever comes next. Shorter, and a list somebody has to
  remember to extend, failing silently each time a file is added to
  `frontend/public/`.
- **Mounting the whole dist as `StaticFiles` with `html=True`**, which serves
  the files but hands the client-route fallback to Starlette, and with it the
  `/api` and `/health` 404 guards this app cannot give up.
