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
| `src/components/layout/` | `Layout` (the navigation from `lib/nav.js`: a top bar on a desktop, a bottom bar on a phone), `LibraryLayout`, `FilterPanel` |
| `src/components/forms/` | `OptionPicker`, `ResourceRows` (the name + link row editor every form with resources uses), `DeleteDialog`, `FormActions` |
| `src/components/ResourceList.jsx` | resources on a detail page |
| `src/lib/links.js` | `isWebLink` and `hostOf`: only an http(s) URL is drawn as a link |
| `src/components/RecordList.jsx` | records as rows, used by the records, exercise and stage pages |
| `src/components/forms/ActivitySelect.jsx` | an exercise, then optionally one of its drills; the record form and the timer use it |
| `src/lib/timer.js`, `src/hooks/useTimer.js`, `src/components/timer/` | the timer's arithmetic and formatting, its context, the top bar chip, and `StartTimerButton` (a drill's 開始計時) |
| `src/components/forms/RecordFields.jsx` | a record's fields but the date and minutes; the record form and the timer's draft both draw them, so the two cannot drift |
| `src/hooks/useRecordDefaults.js`, `src/hooks/useDraftAutosave.js` | the location and tool defaults; saving the timer's draft as it is typed |
| `src/components/forms/RoadmapSelect.jsx` | picks a stage, or a stage or a level for a test |
| `src/lib/records.js`, `src/lib/exercises.js` | every API field those pages read or send, in one place each |
| `src/components/ui/` | `Dialog`, form and display primitives, loading / error / empty states |
| `src/components/Markdown.jsx` | the one Markdown renderer |
| `src/pages/<library|detail|edit|options>/` | one page per file |

There is no route guard and no `/edit` prefix: Cloudflare Access gates the
whole hostname, so every page is the owner's.

**The navigation** is 路線圖 · 練習 · 練法 · 紀錄 · 計時 · 參考 · 筆記 · 選項,
from `lib/nav.js`. On a phone it is a bar fixed to the bottom of the screen;
each entry is at least 3.5rem wide, so its label never truncates, and when
the entries outgrow the screen the bar scrolls sideways (no scrollbar is
drawn) and keeps the active entry in view.

## Pages

| Route | Page |
| --- | --- |
| `/` | redirects to `/roadmap` |
| `/roadmap` | every level in order — code, name, status, description, test — with its stages as rows: number, name, status, test. Everything **in progress** is highlighted wherever it sits — every stage and every level set to 進行中, any number at once — and the stages in progress are listed again at the top as links. Nothing is derived from the order: the owner does not work top to bottom or one stage at a time. Each row changes its status in place (passing it records today) and moves with ↑/↓ |
| `/roadmap/goals/new`, `/roadmap/goals/:id/edit` | goal form; the date appears only for 已達成. Saving or deleting returns to the roadmap |
| `/roadmap/stages/:id` | a stage: description, test, resources, remark, status, its level, its exercises and its test records |
| `/roadmap/stages/new?goal=:id`, `/roadmap/stages/:id/edit` | stage form; changing the level puts the stage last in it |
| `/references` | search box (name, link, notes) and the 參考分組 filter with 未分組, all in the URL; filtering is server-side. Each card: the name, which opens the link itself in a new tab; the link's host; the group chips; the start of the notes; and 詳細, the reference's page |
| `/references/:id` | the reference: the link, its groups (each a link to the library filtered by it), the notes as Markdown, delete |
| `/references/new`, `/references/:id/edit` | one form: name, link (a link with no scheme gets `https://`), groups, notes. Saving goes to the reference's page |
| `/notes` | search box and filter chips for category and topic, all in the URL; filtering is server-side; cards show the name, category, topics and summary |
| `/notes/:id` | the note: summary, Markdown body, resources, remark, delete |
| `/notes/new`, `/notes/:id/edit` | one form: the name, category, topics, summary, body, resources as name + link rows moved with ↑/↓, remark, visibility |
| `/exercises` | grouped by stage in roadmap order, then 不分階段; search and a topic filter in the URL |
| `/exercises/:id` | description, resources, topics, remark; drills as cards (source, unit × target, minutes, frequency, Markdown instructions, links), each with 記錄 → `/records/new?drill=`; the exercise's records and total minutes |
| `/exercises/new`, `/exercises/:id/edit` | exercise form |
| `/drills` | every drill, grouped by its exercise's stage in roadmap order, then 不分階段; search and the 主題 and 來源 filters in the URL. Cards: name, exercise, source, unit × target, minutes, frequency, records and minutes |
| `/drills/:id` | the drill: its exercise and stage, source, instructions, source links, resources, remark, its records; 記錄, 開始計時, 編輯 |
| `/drills/new?exercise=`, `/drills/:id/edit` | drill form: source, source links and resources as two row lists. Saving goes to the drill's page; deleting to its exercise's |
| `/records` | grouped by date, newest first, each day's total (of the records shown, so it follows the filters) and this week's total, Monday to Sunday, from the summary; kind and exercise filters in the URL |
| `/records/new`, `/records/:id/edit` | date (today), location (the most recent record's), tool (Clip Studio Paint), an exercise then optionally one of its drills (`?drill=` or `?exercise=` preselects), kind, a stage or level when 測驗, method with descriptions, minutes, references, notes. The defaults fill only untouched fields |
| `/timer` | with no timer, a start form: stopwatch (the default) or countdown, 10 / 30 minutes or a custom length (the default by weekday: 10 Monday to Friday, 30 at the weekend — a constant in `lib/timer.js` until Schedule owns it), and an optional exercise then drill. With one: large digits, the activity, pause / resume, 停止, 捨棄, and the 紀錄草稿 below it. A countdown past zero keeps counting as `+m:ss` and plays one short tone |
| `/options` | one section per category: its label and description, then its values with description, remark, order and how many places use each (notes, exercises, drills, records, references). Add and edit in place; delete opens a dialog stating the count and sends it with the request. If the count changed, the dialog shows the new one and asks again |

**Every option picker shows the value's description** and links to
`/options`, so what a value means is visible where it is chosen.

**Markdown** (`components/Markdown.jsx`) renders GitHub-flavoured Markdown with
no raw HTML; a `javascript:` link renders inert and other links open in a new
tab. A resource whose URL is not http or https is shown as text, not a link.

## Tests

`npm test` runs Vitest. Page tests go through the real routes with `fetch`
mocked. `Markdown.test.jsx` holds the two safety properties above.

## The timer

The server holds the one running timer; the browser only ticks.
`TimerProvider` (inside `Layout`, so every page has it) reads `/api/timer` on
focus and every 30 seconds and ticks each second while running, offsetting its
clock by the server's `now`. While a timer exists:

- the top bar shows a chip with the activity and the time — on a phone too —
  and 待記錄 once it is stopped;
- the tab title carries the time;
- 開始計時 on a drill starts a stopwatch with that drill, or opens `/timer` if
  a timer already exists.

**The record is written while the timer runs.** Under the clock, 紀錄草稿 holds
the record's fields (`RecordFields`): the activity, kind and test target,
method, location, tool, references and notes, editable in every state. Edits
save themselves 800 ms after the typing stops (`useDraftAutosave`), as the
timer's activity and `draft`, with 儲存中… / 已儲存 beside them. The page adopts
the server's draft once per timer, so the 30-second refetch never overwrites
what is being typed; saves go one at a time; and pause, resume, 停止 and 記錄
send a waiting edit first. 捨棄 drops it.

停止 opens `/records/new?from=timer`: the ordinary record form, prefilled with
the minutes (rounded, at least 1), the date the timer started, and the
activity and draft, saving through `/api/timer/record`. Its edits save to the
draft too, so leaving and coming back loses nothing. Over three hours it warns
beside the duration. Leaving the form keeps the timer stopped.

An edit made under 800 ms before the tab is closed is lost: there is no
`beforeunload` save.

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
