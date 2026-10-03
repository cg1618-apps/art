# API

Every endpoint under `/api`, plus `/health` (see `CLAUDE.md`). There is no
authentication in this app: Cloudflare Access gates the whole hostname, so
reads and writes share one prefix. Tables are in
[data-model.md](data-model.md); vocabularies in [options.md](options.md).

## Conventions

- JSON in and out. A body field this API does not know is a 422.
- **Errors are `{"detail": "<sentence>"}`**, plus extras where named below
  (`app/errors.py`). A request-validation 422 keeps FastAPI's default body,
  where `detail` is a list.

  | Status | Means |
  | --- | --- |
  | 404 | the row in the URL does not exist |
  | 409 | a duplicate, or a stale count on a delete |
  | 422 | the body is wrong: a missing name, an unknown id, an option of the wrong category, an explicit `null` for a list |

- **`PATCH` changes only the fields sent.** A list sent replaces the old one,
  `[]` clears it, and `null` for a list is a 422. Nullable text fields accept
  `null` or `""` to clear them.
- Blank strings are stored as NULL; text is trimmed.

## Goals and stages

`GoalResponse`: `{ id, code, display_name, name_cn, name_en, name_alt,
position, description, test, status, achieved_on, remark, stages }`, where
`stages` are `StageSummary`: `{ id, number, display_name, name_cn, name_en,
name_alt, position, description, test, status, passed_on }`. `number` counts
across the whole roadmap.

`StageResponse`: the summary plus `{ goal: { id, code, display_name }, remark,
resources }`.

| Method | Path | Body / query | Returns |
| --- | --- | --- | --- |
| GET | `/api/goals` | | every goal in order, each with its stages — the whole roadmap |
| GET | `/api/goals/{id}` | | `GoalResponse` |
| POST | `/api/goals` | `{ code, name_cn?, name_en?, name_alt?, position?, description?, test?, status?, achieved_on?, remark? }` | 201. A duplicate `code` is 409 |
| PATCH | `/api/goals/{id}` | the same fields | |
| DELETE | `/api/goals/{id}` | | 204; 409 `{ detail, stages }` while it has stages |
| GET | `/api/stages/{id}` | | `StageResponse` |
| POST | `/api/stages` | `{ goal_id, names…, position?, description?, test?, status?, passed_on?, remark?, resources? }` | 201 |
| PATCH | `/api/stages/{id}` | the same fields | A new `goal_id` moves the stage, last in that goal unless `position` is sent |
| DELETE | `/api/stages/{id}` | | 204 |

- No `position` on create puts the row last. `position` is stored as sent;
  nothing else shifts.
- Setting `status` away from `achieved` / `passed` clears the date. Sending a
  date with any other status is a 422.
- Dates are `YYYY-MM-DD`.

## Options

`OptionResponse`: `{ id, category, value, description, remark, sort_order, in_use }`.
`in_use` counts the notes whose category is the option plus the topic links
naming it — what a delete would remove.

| Method | Path | Body / query | Returns |
| --- | --- | --- | --- |
| GET | `/api/options/categories` | | `[{ key, label, description }]`, in registry order |
| GET | `/api/options` | `?category=` (an unknown one is 422) | options in category order, then `sort_order`, then `id` |
| POST | `/api/options` | `{ category, value, description?, remark?, sort_order? }` | 201. No `sort_order` puts it last in its category. A duplicate value (trimmed, any case) is 409 |
| PATCH | `/api/options/{id}` | `{ value?, description?, remark?, sort_order? }` | Sending `category` at all is a 422: moving a value would leave every link to it in the wrong field |
| DELETE | `/api/options/{id}?in_use=n` | `n` is the count the page showed | 204. Without `in_use`, 422. If the count has changed, 409 `{ detail, field: "in_use", expected, actual }` and nothing is deleted |

## Notes

`NoteSummary`: `{ id, display_name, name_cn, name_en, name_alt, category,
topics, summary, visibility, updated_at }`, where `category` is
`{ id, value, description } | null` and `topics` a list of the same.

`NoteResponse`: the summary plus `{ aliases, body, remark, resources,
created_at }`; `aliases` sorted, `resources` `[{ id, name, url }]` in their
saved order.

| Method | Path | Body / query | Returns |
| --- | --- | --- | --- |
| GET | `/api/notes` | `?q=&category_id=&topic_id=` | summaries ordered by display name |
| GET | `/api/notes/{id}` | | `NoteResponse` |
| POST | `/api/notes` | below | 201 |
| PATCH | `/api/notes/{id}` | the same fields, all optional | `NoteResponse` |
| DELETE | `/api/notes/{id}` | | 204 |

The write body:

```json
{
  "name_cn": "一點透視", "name_en": "one-point perspective", "name_alt": null,
  "aliases": ["1點透視"],
  "category_id": 1,
  "topic_ids": [7],
  "summary": "平行線收斂到地平線上的一個消失點。",
  "body": "1. 設置消失點 ...",
  "remark": null,
  "visibility": "private",
  "resources": [{ "name": "Perspective Art School", "url": "https://www.udemy.com/..." }]
}
```

- At least one of the three names, on create and on the row a `PATCH` leaves.
- `category_id` must name a `note_category` option and `topic_ids` only
  `topic` options; anything else is a 422 naming the id.
- Aliases are trimmed; the same alias twice (any case) is a 422.
- A resource needs a `url`; one with no scheme gets `https://`.

**Search.** `q` matches any name slot, an alias, or the summary, as a
substring, case-insensitively; `%` and `_` are literal. It does not search the
body: a word inside a long note would bury the note you meant. A repeated
`category_id` or `topic_id` means any of them; different filters narrow each
other.
