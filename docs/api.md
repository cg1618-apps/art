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

## Exercises and drills

`ExerciseSummary`: `{ id, display_name, name_cn, name_en, name_alt, stage,
topics, description, drill_count, record_count, total_minutes, updated_at }`,
`stage` being `{ id, number, display_name } | null`. `record_count` and
`total_minutes` count records naming the exercise directly or through any of
its drills.

`ExerciseResponse`: the summary plus `{ aliases, remark, resources, drills,
created_at }`.

`DrillResponse`: `{ id, exercise: { id, display_name }, display_name, name,
source, source_links, resources, instructions, unit, target,
suggested_minutes, frequency, remark, position, created_at, updated_at }`.

| Method | Path | Body / query | Returns |
| --- | --- | --- | --- |
| GET | `/api/exercises` | `?q=&stage_id=&topic_id=&no_stage=true` | summaries by stage number, unstaged last, then name. `q` searches names, aliases and the description |
| GET | `/api/exercises/{id}` | | `ExerciseResponse` |
| POST | `/api/exercises` | `{ name_cn?, name_en?, name_alt?, aliases?, stage_id?, topic_ids?, description?, remark?, resources? }` | 201 |
| PATCH | `/api/exercises/{id}` | the same fields | |
| DELETE | `/api/exercises/{id}` | | 204; 409 `{ detail, drills, records }` while either is non-zero |
| GET | `/api/drills/{id}` | | `DrillResponse` |
| POST | `/api/drills` | `{ exercise_id, name?, source_id?, instructions?, unit?, target?, suggested_minutes?, frequency?, remark?, position?, source_links?, resources? }` | 201 |
| PATCH | `/api/drills/{id}` | the same fields | |
| DELETE | `/api/drills/{id}` | | 204; 409 `{ detail, records }` |

## Records

`RecordResponse`: `{ id, date, kind, activity, stage, goal, location, method,
tool, duration_minutes, references, notes, created_at, updated_at }`.
`activity` is `{ exercise: {id, display_name}, drill: {id, display_name} | null }`,
or null when the record names neither; `stage` and `goal` are set only on a
test.

| Method | Path | Body / query | Returns |
| --- | --- | --- | --- |
| GET | `/api/records` | `?from=&to=&kind=&exercise_id=&drill_id=&stage_id=&goal_id=` | newest first. `exercise_id` matches records naming it directly or through a drill |
| GET | `/api/records/summary` | `?from=&to=` | `[{ date, minutes, records }]`, oldest first, days with records only |
| GET | `/api/records/{id}` | | `RecordResponse` |
| POST | `/api/records` | `{ date, location_id?, duration_minutes?, drill_id?, exercise_id?, kind?, stage_id?, goal_id?, method_id?, tool_id?, references?, notes? }` | 201 |
| PATCH | `/api/records/{id}` | the same fields | |
| DELETE | `/api/records/{id}` | | 204 |

- A drill and an exercise together is a 422.
- A test names exactly one stage or goal; any other kind names neither. Setting
  `kind` away from `test` clears them, unless the same save sends one, which is
  a 422.
- Option fields take their own category only: `location`, `method`, `tool`
  here, `source` on a drill.
- Deleting a stage or goal named by records is a 409 `{ detail, records }`; a
  goal with stages keeps its `{ detail, stages }`, checked first.

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
