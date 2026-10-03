# Notes + Options — design

The first module. It builds the open vocabulary every later module reads
(system options), the page that manages it, and Notes: knowledge that is not
tied to any one record, tool or reference — terms, tips, advice, notes in
general.

Working scaffolding: deleted when the module lands, with what survives moved
into `docs/data-model.md`, `docs/api.md`, `docs/options.md`,
`docs/frontend.md` and `docs/notes/decisions.md`.

## Why this module comes first

Every later module — Roadmap, Record, Drill, Tool, Reference — reads system
options (method, location, tool, source, topic). Options are groundwork either
way, and the page that manages them costs little more when it is built
alongside the first module that uses them.

The module order this sets, recorded in `decisions.md` when it lands:

**Notes + Options** → Goals → Roadmap → Schedule → Record + Exercise/Drill →
Timer → Tool → Reference → Plan to draw → Artist → Works. The first build
block ends at Reference.

## Options

### Three tiers, as in `media`

The same question decides where a list lives: **does code branch on the exact
value?**

| Tier | Lives in | Changed by | Examples here |
| --- | --- | --- | --- |
| 1 | Python constants in `app/constants.py` | a code change | `visibility` (`private` / `unlisted` / `public`), the option **categories** themselves |
| 2 | `system_option` rows | the Options page | 名詞, 小技巧, 速寫, 透視 |
| 3 | entity tables | their own module | (none yet; artists, tools later) |

### Categories are a registry in code

Unlike `media`, where `category` is free text on the API, a category here must
be one the code registers. Every category is read by some field, so a category
nobody reads is a typo; and a category needs a label and a description of its
own (the page explains what "Method" means before listing its values).

```python
@dataclass(frozen=True)
class OptionCategory:
    key: str          # stored in system_option.category
    label: str        # 筆記分類
    description: str  # shown above the category's values on the Options page

OPTION_CATEGORIES = {c.key: c for c in (...)}
```

Categories this module registers:

| key | label | read by | seeded values |
| --- | --- | --- | --- |
| `note_category` | 筆記分類 | `note.category_id` | 名詞, 知識, 小技巧, 建議 |
| `topic` | 主題 | note tags | 線條, 形狀, 透視, 比例, 人體, 動態, 構圖, 光影, 色彩, 特效 |
| `method` | 方法 | `record.method_id` (Record module) | the seven below |

`method` is registered now, before anything reads it, so its descriptions are
on the Options page from the first release. Later modules add `location`,
`tool`, `source` and their own tag categories the same way.

Seeded `method` values, in this order, with these descriptions:

| value | description |
| --- | --- |
| 臨摹 | 直接在參考圖上方描繪，盡量完整還原。（很少使用） |
| 重現 | 不疊在參考圖上，看著參考圖盡量完整還原整張圖，例如動畫截圖。屬於描寫的一種。 |
| 描寫 | 看著參考圖畫，不疊在參考圖上。不要求完整還原。 |
| 速寫 | 限時快速畫，抓動態和大形，不追求細節。 |
| 同人創作 | 以既有角色或作品為題材的創作：構圖和姿勢是自己的，對象是別人的。 |
| 原創創作 | 原創題材，例如自己的原創角色。可以使用參考資料。 |
| 隨便畫 | 沒有特定目標，想畫什麼就畫什麼。 |

### `system_option`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | integer | no | PK |
| `category` | text | no | a key of `OPTION_CATEGORIES`; CHECK built from the registry (`in_clause`, as `travel`) |
| `value` | text | no | what is displayed |
| `description` | text | yes | **what the value means**, shown on the Options page and as the picker's tooltip |
| `remark` | text | yes | a note to yourself; not shown outside the Options page |
| `sort_order` | integer | no | default 0; the order inside a category |
| `created_at`, `updated_at` | timestamptz | no | database clock (`TimestampMixin`, as `travel`) |

- `uq_system_option_value`: unique on `(category, lower(value))` — `速寫` and
  ` 速寫 ` are one value after trimming, and `Hand` / `hand` are one value.
- No scope, usage or alias tables. They answer questions `media` has (which
  media type, which source field, which external API string) that art does
  not. Added when a question needs them, not before.

Divergences from `media`, each recorded in `decisions.md`:

- **Integer `id`**, not a UUID `system_id`: art's skeleton is `travel`'s, and
  every table in `travel` and `food` uses integer ids.
- **`description` beside `remark`.** `media`'s `remark` is an admin note, shown
  read-only on one page. A description is the opposite: written for the moment
  you pick the value. Two audiences, two columns.
- **Categories are registered in code**, above.
- **Delete is guarded by a count**, below. `media` deletes silently and
  cascades the tags away.

### Rules

- **Entities link to options by id**, never by copying the text. A rename is
  therefore one row and shows everywhere at once.
- **A field accepts only options of its own category.** `note.category_id`
  naming a `topic` option is a 422, as is a topic tag naming a `method` option.
  Checked in the service, since a FK cannot see the category.
- **Deleting an option in use states how much it removes.** `DELETE` takes
  `in_use=<n>`, the count the page showed; the server recounts and refuses with
  409 (`field`, `expected`, `actual`, as `food`'s `StaleCountError`) when they
  differ. On success, tag links cascade away and single-valued references
  (`note.category_id`) are set NULL. The confirm dialog says what will happen:
  "3 筆記 will lose this tag".
- Creating a duplicate value in a category is 409.

## Notes

### `note`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | integer | no | PK |
| `name_cn`, `name_en`, `name_alt` | text | yes | at least one (`ck_note_has_a_name`); not unique — `food`'s dish shape |
| `category_id` | integer | yes | → `system_option`, `ON DELETE SET NULL`; must be a `note_category` option |
| `summary` | text | yes | one or two sentences. For a 名詞, its definition. Shown in lists and tooltips |
| `body` | text | yes | Markdown: steps, examples, your own understanding |
| `remark` | text | yes | |
| `visibility` | text | no | `private` / `unlisted` / `public`, default `private`; CHECK from the enum |
| `created_at`, `updated_at` | timestamptz | no | |

`display_name` is `name_cn`, else `name_en`, else `name_alt` —
`NameFallbackMixin`, as `food`.

**Category is optional.** None of this app may demand bookkeeping before it is
useful: a note is worth writing before you have decided what kind it is.

**`visibility` is here from the first migration** and nothing reads it yet.
`CLAUDE.md` expects notes worth sharing; the column is free now, and the checks
at every read path are what is expensive to retrofit. The `/s/...` routes come
with Works, and with them the refusal tests.

### Children

| Table | Columns | Notes |
| --- | --- | --- |
| `note_alias` | `id`, `note_id` (CASCADE), `value` | `uq_note_alias (note_id, value)`, `ix_note_alias_lookup (lower(value))`; never displayed, searched. `food`'s `dish_alias` |
| `note_resource` | `id`, `note_id` (CASCADE), `position`, `name` (null), `url` | `ck_note_resource_has_a_url (btrim(url) <> '')`; the list is replaced whole on save. `food`'s `tbd_link`, with `label` renamed `name` — "label" is a tag word here |
| `note_topic` | `note_id` (CASCADE), `option_id` (CASCADE), composite PK | `ix_note_topic_option (option_id)`; options of category `topic` only |

### Search

`GET /api/notes?q=&category_id=&topic_id=` — server-side, as `food`:

- `q` matches `ilike` over the three name slots, the aliases, and `summary`.
  Not `body`: a word inside a long note would bury the note you meant.
- Repeated `topic_id` means any of them; `category_id` likewise.
- No pagination; ordered by `display_name`.

## API

All bodies are JSON; every error is `{"detail": "<sentence>"}` plus extras.
404 for a missing row, 422 for validation and wrong-category ids, 409 for a
duplicate or a stale count.

| Method | Path | |
| --- | --- | --- |
| GET | `/api/options/categories` | the registry: key, label, description |
| GET | `/api/options` | every option, `?category=` to narrow; each with `in_use` |
| POST | `/api/options` | 201 |
| PATCH | `/api/options/{id}` | `category` cannot change: moving a value between categories would leave every link to it in the wrong field |
| DELETE | `/api/options/{id}?in_use=n` | 204 |
| GET | `/api/notes` | summaries |
| GET | `/api/notes/{id}` | full note, topics and resources expanded |
| POST | `/api/notes` | 201 |
| PATCH | `/api/notes/{id}` | only the fields sent; a list sent replaces the old one, `[]` clears it, `null` for a list is 422 |
| DELETE | `/api/notes/{id}` | 204 |

There is no `/api/edit` split as in `food`: `food` is public and gates writes
under that prefix; art is behind Cloudflare Access whole, and publishing will
use `/s/...` for reads instead.

## Frontend

Nothing exists yet but a health line, so this module lays the foundation, and
copies `food`'s rather than `media`'s, because `food`'s is the newer, smaller
version of the same ideas (one `client.js` that calls `fetch`,
`endpoints.js`, `useApiQuery` / `useApiMutation` over TanStack Query,
`useUrlFilters`, react-router 7, Tailwind 4, Vitest). `media`'s Options page
uses raw `fetch` in `useEffect` and react-router 6 — the older shape, which
`media` has not revisited rather than chosen.

Markdown: `react-markdown` + `remark-gfm`, configured as `media`'s
`ResourceMarkdown` — no raw HTML, the default URL transform (so `javascript:`
links render inert), links opened in a new tab.

| Route | Page |
| --- | --- |
| `/` | redirects to `/notes` until a later module owns the home page |
| `/notes` | list: search box, category and topic filter chips (in the URL), cards with name, category, topics, summary |
| `/notes/new`, `/notes/:id/edit` | form page: names, aliases (one box, split on `,，、` and newlines, as `food`), category, topics, summary, body, resources (name + link rows, add/remove/reorder), remark |
| `/notes/:id` | detail: everything above, body rendered as Markdown |
| `/options` | one section per category: label, its description, then a table of values (value, description, remark, order, in use). Add, edit and delete in place; delete opens a dialog stating the count |

A shell with a top navigation (Notes, Options) that later modules extend.

**Option pickers show the description.** Wherever a field picks an option, the
picker shows that value's description as a tooltip and links to `/options`.

## Tests

- Backend, per `food`'s layout: `tests/api/` with `db` and `client` fixtures,
  one transaction rolled back per test.
- **Refusal tests make refusal possible.** The wrong-category tests create an
  option of *another* category first; a category check over an empty table
  passes without firing. Each has its mirror (the right category is accepted)
  using the same fixture.
- The delete count: a stale count refuses, the right one deletes, and the tags
  and the category reference are gone afterwards.
- `tests/test_migrations_build_the_schema.py` keeps proving the chain from zero.
- Frontend: a test that the Markdown renderer drops raw HTML and makes a
  `javascript:` link inert.

## Out of scope

Images on notes; links from a note to a stage, exercise or tool (tags cover
it until a module needs more); sharing routes; merging two options; option
aliases and scopes.
