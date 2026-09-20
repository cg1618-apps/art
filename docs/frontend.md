# Frontend

React + Vite. No module is built yet, so there are no pages or components to
describe; the conventions, when there are, are `media`'s, per the platform's
house-style section. What is here is what is true of the frontend now: how the
built bundle reaches a browser.

## How the built bundle is served

**One process serves the API and the bundle, and nothing sits in front of it** —
cloudflared connects straight to uvicorn, so there is no proxy to serve a static
file this app declines to. `app/main.py` is the whole story:

- **`/assets/...`** is mounted as `StaticFiles`, when the build produced an
  `assets/` directory at all. Vite inlines every asset when the bundle is small
  enough, so the mount is conditional.
- **`/api/...` and `/health/...`** are refused by the catch-all with a 404, even
  when unregistered. This app's health path is `/health`, not `/api/health`, so
  a mistyped probe path must not come back as a 200 carrying the bundle.
- **Any other path that names a real file inside the bundle is served as that
  file** — `favicon.svg`, `favicon.ico`, `robots.txt`, anything the build copies
  from `frontend/public/` to the root of `frontend_dist/`. The path is resolved
  and confined to the dist directory first, so `..%2F.env` cannot read a file
  beside the bundle.
- **Everything else is `index.html`**, so client-side routing works.

The order matters and is the same as `media`'s: the health router is registered
before the catch-all, so it cannot shadow a route that exists.

**A file in `frontend/public/` reaches production only through this handler.**
Before it served real files, `/favicon.svg` answered with `index.html` under
`text/html` and the browser discarded it — the icon was in the repository and in
the bundle, and had never once been shown.

## The icon

`frontend/public/favicon.svg` is the cg1618 icon, the same artwork the platform's
apex page and the other apps carry. `favicon.ico` sits beside it for the
browsers and the pinned-tab cases that ask for one; `frontend/index.html`
declares both, the SVG first.

## After any frontend change

```bash
cd frontend && npm run build               # writes frontend_dist/ for uvicorn
```

uvicorn on 8003 serves the prebuilt bundle; the Vite dev server on 5176 does
not use it. A change that appears on one port only is a stale build.
