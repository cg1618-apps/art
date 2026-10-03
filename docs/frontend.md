# Frontend

React + Vite, with `food`'s foundation: react-router 7, TanStack Query,
Tailwind 4 with `food`'s design tokens, Vitest. Why `food`'s and not
`media`'s is in `notes/decisions.md`. UI text is Traditional Chinese.

## Layout

| Path | Holds |
| --- | --- |
| `src/routes.jsx` | the route table |
| `src/api/client.js` | **the only file that calls `fetch`**; errors carry `.status` and `.body` |
| `src/api/endpoints.js` | every API URL |
| `src/hooks/useApi.js` | `useApiQuery`, `useApiMutation`, `useOptionCategories`, `useOptions(category)` |
| `src/hooks/useUrlFilters.js` | search and filters kept in the URL: typing replaces the history entry (debounced), a filter click pushes one |
| `src/components/layout/` | `Layout` (top nav from `lib/nav.js`), `LibraryLayout`, `FilterPanel` |
| `src/components/forms/` | `OptionPicker`, `ResourceRows` (the name + link row editor every form with resources uses), `DeleteDialog`, `FormActions` |
| `src/components/ResourceList.jsx` | resources on a detail page |
| `src/components/ui/` | `Dialog`, form and display primitives, loading / error / empty states |
| `src/components/Markdown.jsx` | the one Markdown renderer |
| `src/pages/<library|detail|edit|options>/` | one page per file |

There is no route guard and no `/edit` prefix: Cloudflare Access gates the
whole hostname, so every page is the owner's.

## Pages

| Route | Page |
| --- | --- |
| `/` | redirects to `/roadmap` |
| `/roadmap` | every level in order — code, name, status, description, test — with its stages as rows: number, name, status, test. The **current stage**, the first not passed in roadmap order, is marked. Each row changes its status in place (passing it records today) and moves with ↑/↓ |
| `/roadmap/goals/new`, `/roadmap/goals/:id/edit` | goal form; the date appears only for 已達成. Saving or deleting returns to the roadmap |
| `/roadmap/stages/:id` | a stage: description, test, resources, remark, status, its level |
| `/roadmap/stages/new?goal=:id`, `/roadmap/stages/:id/edit` | stage form; changing the level puts the stage last in it |
| `/notes` | search box and filter chips for category and topic, all in the URL; filtering is server-side; cards show the name, category, topics and summary |
| `/notes/:id` | the note: summary, Markdown body, resources, remark, delete. Aliases are not shown: they exist to be searched |
| `/notes/new`, `/notes/:id/edit` | one form: three names, aliases in one box (split on `,`, `，`, `、` and newlines), category, topics, summary, body, resources as name + link rows moved with ↑/↓, remark, visibility |
| `/options` | one section per category: its label and description, then its values with description, remark, order and how many notes use each. Add and edit in place; delete opens a dialog stating the count and sends it with the request. If the count changed, the dialog shows the new one and asks again |

**Every option picker shows the value's description** and links to
`/options`, so what a value means is visible where it is chosen.

**Markdown** (`components/Markdown.jsx`) renders GitHub-flavoured Markdown with
no raw HTML; a `javascript:` link renders inert and other links open in a new
tab. A resource whose URL is not http or https is shown as text, not a link.

## Tests

`npm test` runs Vitest. Page tests go through the real routes with `fetch`
mocked. `Markdown.test.jsx` holds the two safety properties above.

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
