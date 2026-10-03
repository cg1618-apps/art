# Data model

Every table, what it holds, and the constraints that hold it. The vocabularies
the tables draw on are listed in [options.md](options.md); the endpoints that
read and write them in [api.md](api.md).

Models are in `app/models/`; the schema is built by Alembic
(`alembic/versions/`), and `tests/test_migrations_build_the_schema.py` proves
the chain builds from zero and matches the models.

## Tables

- [`goal`](#goal) — a level of the roadmap, L0 to L5
- [`stage`](#stage) — one stage of a level, with its test
- [`stage_resource`](#stage_resource) — the links kept with a stage
- [`system_option`](#system_option) — one value of an open vocabulary
- [`note`](#note) — a piece of knowledge: a term, a tip, advice, a note
- [`note_alias`](#note_alias) — names a note can be searched by
- [`note_resource`](#note_resource) — the links kept with a note
- [`note_topic`](#note_topic) — a note's topic tags

```mermaid
flowchart TD
    O["system_option"] -->|category_id, ON DELETE SET NULL| N["note"]
    N -->|note_id, CASCADE| A["note_alias"]
    N -->|note_id, CASCADE| R["note_resource"]
    N -->|note_id, CASCADE| T["note_topic"]
    O -->|option_id, CASCADE| T
    G["goal"] -->|goal_id, RESTRICT| S["stage"]
    S -->|stage_id, CASCADE| SR["stage_resource"]
```

**What a note owns cascades with it; what it names gives way.** Aliases,
resources and topic links go when the note goes. Deleting an option sets
`note.category_id` NULL and removes the topic links naming it — a note is worth
keeping without them.

Every table carries `created_at` and `updated_at` except the link and child
tables; both are `timestamptz` defaulted by the database clock
(`TimestampMixin`, `app/models/base.py`).

## `goal`

A level: what you can draw at the end of it, and the test that shows it.

| Column | Type | Null | Default | Notes |
| --- | --- | --- | --- | --- |
| `id` | integer | no | | |
| `code` | text | no | | `L0` … `L5`; unique as written (`uq_goal_code`), trimmed |
| `name_cn`, `name_en`, `name_alt` | text | yes | | At least one (`ck_goal_has_a_name`) |
| `position` | integer | no | | Order on the roadmap. Created without one, it goes last |
| `description` | text | yes | | Done when you can … |
| `test` | text | yes | | The test piece |
| `status` | text | no | `planned` | `planned`, `active`, `achieved` (`ck_goal_status`) |
| `achieved_on` | date | yes | | Only with `achieved` (`ck_goal_achieved_on_iff_achieved`); achieved may leave it empty |
| `remark` | text | yes | | |

**Status is set by hand.** Nothing derives it from the stages: a level is
passed on its test, which may come before every stage is ticked.

**A goal with stages cannot be deleted** (`stage.goal_id` is `RESTRICT`); the
API says how many stages are in the way.

## `stage`

| Column | Type | Null | Default | Notes |
| --- | --- | --- | --- | --- |
| `id` | integer | no | | |
| `goal_id` | integer | no | | → `goal`, `RESTRICT`, indexed |
| `position` | integer | no | | Order inside its goal; last when not given |
| `name_cn`, `name_en`, `name_alt` | text | yes | | At least one (`ck_stage_has_a_name`) |
| `description` | text | yes | | What is practised |
| `test` | text | yes | | The stage's test |
| `status` | text | no | `not_started` | `not_started`, `in_progress`, `passed` (`ck_stage_status`) |
| `passed_on` | date | yes | | Only with `passed`, as `achieved_on` |
| `remark` | text | yes | | |

**The stage number is derived, never stored**: every stage ordered by goal
position, goal id, stage position, stage id, numbered from 0. Moving a stage
renumbers everything after it.

## `stage_resource`

The `note_resource` shape: `id`, `stage_id` (`CASCADE`), `position`, `name`,
`url` (`ck_stage_resource_has_a_url`). The lectures worth rewatching when the
stage starts.

## The roadmap seed

Migration `0003_goals_and_roadmap` writes the roadmap agreed with the owner:
six goals (L0 基礎, L1 人體, L2 角色, L3 場景, L4 上色, L5 插畫) and sixteen
stages numbered 0 to 15, with their descriptions and tests; L0 `active`,
everything else not started. It is the seed, not the truth — the roadmap pages
edit it — and it is idempotent, keyed on the goal code and on goal plus
`name_cn` for a stage.

## `system_option`

| Column | Type | Null | Default | Notes |
| --- | --- | --- | --- | --- |
| `id` | integer | no | | |
| `category` | text | no | | A key of `OPTION_CATEGORIES` (`app/constants.py`); `ck_system_option_category` is built from the registry. |
| `value` | text | no | | What is displayed. Trimmed on the way in. |
| `description` | text | yes | | What the value means, shown on the Options page and in every picker. |
| `remark` | text | yes | | A note to yourself; the Options page only. |
| `sort_order` | integer | no | `0` | Order inside the category. A value created without one goes last. |

`uq_system_option_value` is a unique index on `(category, lower(btrim(value)))`:
`速寫` and ` 速寫 `, `Hand` and `hand`, are one value.

**Entities link to an option by id, never by copying its text**, so renaming a
value is one row and shows everywhere at once. Which category a field accepts
is checked in the service (a foreign key cannot see the category).

## `note`

| Column | Type | Null | Default | Notes |
| --- | --- | --- | --- | --- |
| `id` | integer | no | | |
| `name_cn`, `name_en`, `name_alt` | text | yes | | At least one (`ck_note_has_a_name`). **Not unique.** |
| `category_id` | integer | yes | | → `system_option`, `ON DELETE SET NULL`, indexed. A `note_category` option. |
| `summary` | text | yes | | One or two sentences; a 名詞's definition. Shown in lists and searched. |
| `body` | text | yes | | Markdown. Not searched. |
| `remark` | text | yes | | |
| `visibility` | text | no | `private` | `private`, `unlisted` or `public` (`ck_note_visibility`). Nothing reads it yet. |

`display_name` is `name_cn`, else `name_en`, else `name_alt`
(`NameFallbackMixin`).

**The category is optional**: a note is worth writing before you decide what
kind it is.

**`visibility` is reserved.** It exists so that sharing, when it is built, adds
checks rather than a column; see `CLAUDE.md`, "Who can see it".

## `note_alias`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | integer | no | |
| `note_id` | integer | no | → `note`, `CASCADE`, indexed |
| `value` | text | no | |

Anything you might type to find a note; searched, never displayed.
`uq_note_alias` on `(note_id, value)`; `ix_note_alias_lookup` on `lower(value)`.
A save reconciles the list by value, so an unchanged alias keeps its row.

## `note_resource`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | integer | no | |
| `note_id` | integer | no | → `note`, `CASCADE`, indexed |
| `position` | integer | no | The order sent. No unique constraint: the list is replaced whole on a save. |
| `name` | text | yes | |
| `url` | text | no | `ck_note_resource_has_a_url` (`btrim(url) <> ''`). http or https; a URL with no scheme is stored with `https://`. |

## `note_topic`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `note_id` | integer | no | → `note`, `CASCADE`; part of the PK |
| `option_id` | integer | no | → `system_option`, `CASCADE`; part of the PK; `ix_note_topic_option` |

`topic` options only. Returned ordered by the option's `sort_order`.
