# Notes + Options — implementation plan

Executes `docs/superpowers/specs/2026-10-03-notes-and-options-design.md`.
Branch `feat/notes-and-options`. Deleted with the spec when the module lands.

Two tracks run in parallel in the same tree, split by directory so they cannot
touch each other's files. Docs are written last, by the main session.

## The contract both tracks build against

JSON field names, exactly:

```text
OptionCategory   { key, label, description }
Option           { id, category, value, description, remark, sort_order, in_use }
OptionWrite      POST: { category, value, description?, remark?, sort_order? }
                 PATCH: { value?, description?, remark?, sort_order? }   (category is 422)
OptionRef        { id, value, description }

NoteSummary      { id, display_name, name_cn, name_en, name_alt,
                   category: OptionRef | null, topics: [OptionRef],
                   summary, visibility, updated_at }
Note             NoteSummary + { aliases: [str], body, remark,
                   resources: [{ id, name, url }], created_at }
NoteWrite        { name_cn?, name_en?, name_alt?, aliases?: [str],
                   category_id?: int | null, topic_ids?: [int],
                   summary?, body?, remark?, visibility?,
                   resources?: [{ name?: str | null, url: str }] }

Errors           { "detail": "<sentence>" } plus extras;
                 stale delete count: 409 { detail, field: "in_use", expected, actual }
```

Routes:

```text
GET    /api/options/categories
GET    /api/options[?category=]
POST   /api/options                    201
PATCH  /api/options/{id}
DELETE /api/options/{id}?in_use=n      204 | 409 stale | 422 missing in_use
GET    /api/notes[?q=&category_id=&topic_id=]   repeated ids = any of
GET    /api/notes/{id}
POST   /api/notes                      201
PATCH  /api/notes/{id}
DELETE /api/notes/{id}                 204
```

`in_use` on an option = notes whose `category_id` is it + `note_topic` rows
naming it.

## Track A — backend (owns `app/`, `alembic/`, `tests/`, `requirements*.txt`)

1. `app/constants.py`: `Visibility` StrEnum; `OptionCategory` dataclass and
   `OPTION_CATEGORIES` (`note_category`, `topic`, `method`) with labels and
   descriptions from the spec.
2. `app/models/`: `base.py` (`TimestampMixin`, `in_clause`,
   `NameFallbackMixin` — copied from `travel` / `food`), `system_option.py`,
   `note.py` (`Note`, `NoteAlias`, `NoteResource`, `NoteTopic`). Constraint
   names as the spec.
3. Migration `0002_notes_and_options`: the tables, then the seed in raw SQL
   with frozen constants and no app imports, idempotent (`WHERE NOT EXISTS`),
   as `media`'s seeds. `downgrade` drops the tables.
4. `app/errors.py`: `AppError` and the handler, `{"detail"}` plus extras, and
   the IntegrityError backstop — copied from `food`.
5. `app/schemas/`, `app/services/options.py`, `app/services/notes.py`,
   `app/routers/options.py`, `app/routers/notes.py`; registered in
   `create_app` **before** the SPA catch-all.
6. Tests in `tests/api/`: conftest with `test_engine` / `db` / `client` as
   `food`'s (an `art_test` database, `create_all`). Cover: CRUD round trips,
   name required, alias duplicates, wrong-category refusals **with an option of
   the other category present** and their mirrors, PATCH `category` refused,
   duplicate value 409 (case and whitespace), delete count stale/right with
   cascade and SET NULL, search over names / aliases / summary but not body,
   topic and category filters, resources replaced whole and ordered, `null`
   list refused, 404s. The from-zero migration test must stay green.
7. `ruff check .` clean; pytest under the machine-wide lock.

## Track B — frontend (owns `frontend/`)

1. Dependencies: react-router-dom 7, @tanstack/react-query 5, tailwindcss 4 +
   @tailwindcss/vite, react-markdown, remark-gfm, vitest + testing-library —
   versions as `food`'s `package.json`.
2. Foundation copied from `food`'s shape: `src/api/client.js`,
   `src/api/endpoints.js`, `src/hooks/useApi.js`, `src/hooks/useUrlFilters.js`,
   `src/routes.jsx`, a layout shell with top nav (筆記, 選項).
3. `src/components/Markdown.jsx` as `media`'s `ResourceMarkdown`, with its test.
4. Pages: `pages/library/NoteLibrary.jsx`, `pages/detail/Note.jsx`,
   `pages/edit/NoteForm.jsx`, `pages/options/Options.jsx`; an `OptionPicker`
   that shows the description as a tooltip and links to `/options`.
5. `npm run lint`, `npm test`, `npm run build` all pass.

## Finish (main session)

- `docs/data-model.md`, `docs/api.md`, `docs/options.md`, `docs/frontend.md`,
  `docs/README.md`, `docs/notes/decisions.md` (module order, divergences from
  `media`, the frontend foundation choice), `CLAUDE.md` status line.
- Delete this plan and the spec in the same commit.
- PR into `dev`.
