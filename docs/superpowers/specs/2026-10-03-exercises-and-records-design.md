# Record + Exercise — design

Module 5 of `docs/notes/decisions.md`, "Structure". Working scaffolding;
deleted when the module lands. Builds on Goals + Roadmap (`stage`, `goal`) and
Notes + Options (`system_option`).

## What the owner agreed

- **Exercise (練習項目) and Drill (練法)** are `food`'s dish and recipe. An
  exercise is what is practised; a drill is one prescribed way of doing it.
  "Exercise type" was renamed: the general thing is the Exercise.
- An exercise has names, an optional stage, a description, **resources**
  (name–link pairs), a **remark**, and tags.
- A drill has its exercise (required), an optional name falling back to the
  exercise's, a **source** option, **source links** (name–link pairs), **resources**
  (name–link pairs), instructions, unit, target, suggested minutes, frequency,
  and a **remark**.
- **One record per exercise practised.** A record names a drill, an exercise,
  or neither — never both; through a drill the exercise is derived.
- Record fields: date, **location** (kept from the old sheet), duration in
  minutes (optional), kind, method, tool, **reference links** (name–link pairs,
  several), notes. No "finished unit", no "what looked weird" tags. Images are
  designed later (Google Drive / Google Photos).
- Method values and their descriptions are already seeded (Notes + Options).
- The old spreadsheet log is **not** migrated.

## Options this module registers

| key | label | read by | seeded values |
| --- | --- | --- | --- |
| `source` | 來源 | `drill.source_id` | Character Art School, Character Art School: Coloring, Manga Art School, Perspective Art School, 自訂, 其他 |
| `location` | 地點 | `record.location_id` | 台灣・家, 美國・家 |
| `tool` | 工具 | `record.tool_id` | Clip Studio Paint, Procreate, 紙筆 |

Exercise tags reuse `topic` (主題), as notes do.

Adding categories means replacing `ck_system_option_category` in the
migration (see `docs/options.md`).

## Tables

### `exercise`

| Column | Notes |
| --- | --- |
| `id` | |
| `name_cn`, `name_en`, `name_alt` | at least one (`ck_exercise_has_a_name`) |
| `stage_id` | → `stage`, `ON DELETE SET NULL`, indexed, nullable. Warm-ups and gesture, practised at every level, have none |
| `description` | |
| `remark` | |
| timestamps | |

Children: `exercise_alias` (as `note_alias`), `exercise_resource` (as
`note_resource`), `exercise_topic` (as `note_topic`, `topic` options only).

### `drill`

| Column | Notes |
| --- | --- |
| `id` | |
| `exercise_id` | → `exercise`, `RESTRICT`, indexed, required |
| `name` | optional; `display_name` falls back to the exercise's |
| `source_id` | → `system_option`, `SET NULL`; a `source` option |
| `instructions` | text (Markdown) |
| `unit` | text: 頁, 張, 組, 個 |
| `target` | integer ≥ 1, nullable: how many units make one round |
| `suggested_minutes` | integer ≥ 1, nullable |
| `frequency` | text: "daily for 3 weeks", 每天 |
| `remark` | |
| `position` | order inside its exercise |
| timestamps | |

Children: `drill_source_link` and `drill_resource`, both the `note_resource`
shape.

### `record`

| Column | Notes |
| --- | --- |
| `id` | |
| `date` | date, required |
| `location_id` | → option, `SET NULL`; a `location` option |
| `duration_minutes` | integer ≥ 0, nullable |
| `drill_id` | → `drill`, `RESTRICT` |
| `exercise_id` | → `exercise`, `RESTRICT` |
| `kind` | `practice` / `piece` / `test` (Tier 1 `RecordKind`, labels 練習 / 作品 / 測驗), default `practice` |
| `stage_id` | → `stage`, `RESTRICT`; the stage whose test this is |
| `goal_id` | → `goal`, `RESTRICT`; the level whose test this is |
| `method_id` | → option, `SET NULL`; a `method` option |
| `tool_id` | → option, `SET NULL`; a `tool` option |
| `notes` | |
| timestamps | |

- `ck_record_one_activity`: `num_nonnulls(drill_id, exercise_id) <= 1`.
- `ck_record_test_target`: `(kind = 'test') = (num_nonnulls(stage_id, goal_id) = 1)`, and
  neither is set otherwise. A test record is the test of exactly one stage or
  one level.
- Indexes on `date`, `drill_id`, `exercise_id`, `stage_id`, `goal_id`.

Child: `record_reference` (the `note_resource` shape): the reference links.

**Records RESTRICT what they name.** A record is history: deleting the drill,
exercise, stage or goal it names is a 409 stating how many records name it,
never a silent loss. Deleting an exercise that still has drills is a 409 too.

`activity` in responses: `{exercise: {id, display_name}, drill: {id,
display_name} | null}` derived from whichever is set.

## Seed

Exercises and drills from the owner's notes (`細節指示`) and the Udemy
assignment sheet — source, minutes and frequency as the sheet gives them; a
range takes its lower bound in `suggested_minutes`, with the sheet's wording in
`frequency`. Listed in `SEED` in the migration; the table below is the
content.

Stages are named by their seeded `name_cn` (the migration finds them by
goal code + `name_cn`; a stage the owner renamed is skipped, leaving the
exercise without a stage, never failing). Sources: CAS = `Character Art
School`, MAS = `Manga Art School`, PAS = `Perspective Art School`, 自訂 =
the owner's own. Drill `position` is the order listed. Every string is copied
verbatim.

| # | Exercise 中文 / English | Stage | Description |
| --- | --- | --- | --- |
| 1 | 線條 / Lines | 線條與形狀 | 穩定的直線與曲線，用手肘和肩膀畫，不用手腕。 |
| 2 | 2D 形狀 / 2D shapes | 線條與形狀 | 平面的基本形狀，由小到大。 |
| 3 | 用線條概括 / Summarise with lines | 線條與形狀 | 用最少的線抓住物體的大結構。 |
| 4 | 基本形體 / Basic forms | 空間中的形體 | 方塊、球體、圓柱、圓錐，不同角度。 |
| 5 | 透視方塊 / Boxes in perspective | 空間中的形體 | 一點、兩點、三點透視中的方塊與堆疊。 |
| 6 | 人體比例 / Body proportion | 比例 | 以頭身為單位的人體比例。 |
| 7 | 人偶 / Mannequin | 比例 | 從動態線到人偶的五個步驟。 |
| 8 | 動態速寫 / Gesture drawing | — | 限時抓動態。每個等級都練，所以不屬於任何階段。 |
| 9 | 動態形狀與形體 / Dynamic gestures | 動態到人偶 | 把動態轉成形狀，再轉成形體。 |
| 10 | 鏡頭與視角 / Camera and view | 透視中的人體 | 鏡頭角度、視錐與空間分區。 |
| 11 | 透視中的人體 / Figure in perspective | 透視中的人體 | 完整形體的人體放進透視。 |
| 12 | 肌肉量塊 / Muscle masses | 主要肌肉量塊 | 疊在動態上的主要肌群量塊。 |
| 13 | 頭部 / Head | 頭部、五官、表情 | 任何角度的頭部與五官。 |
| 14 | 表情 / Expression | 頭部、五官、表情 | 表情與情緒。 |
| 15 | 手 / Hands | 手與腳 | 手的比例與結構。 |
| 16 | 頭髮 / Hair | 完稿：頭髮、衣服、配件 | 頭髮的大形與設計。 |
| 17 | 衣服與衣褶 / Clothing and folds | 完稿：頭髮、衣服、配件 | 衣褶種類與穿在人體上的衣服。 |
| 18 | 完稿流程 / Workflow | 完稿：頭髮、衣服、配件 | 從草稿到線稿的流程。 |
| 19 | 環境透視技巧 / Environment perspective | 環境透視 | 找中心、複製平面、縮放與透視中的橢圓。 |
| 20 | 構圖 / Composition | 構圖與角色入景 | 結合構圖理論，角色半身作品。 |
| 21 | 色彩複製 / Colour matching | 色彩 | 判斷並複製顏色：先色相，再明度。 |
| 22 | 角色作品 / Character piece | — | 一張完整的角色，粗糙也沒關係。每個等級都畫。 |
| 23 | 視覺資料庫 / Visual library | — | 依主題累積看過、畫過的東西。 |
| 24 | 對照畫 / Comparative drawing | — | 同一張圖隔一段時間再畫一次，比較進步。 |

Drills (exercise #, name, source, unit, target, suggested_minutes, frequency, instructions):

| Ex | Name | Source | Unit | Target | Min | Frequency | Instructions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 基本線條 | 自訂 | 頁 | 1 | 10 | 每天（暖身） | 直線（水平、垂直、斜線，兩個方向）、1/4 圓弧、半圓弧、波浪線、鋸齒線。長短、輕重各練。 |
| 1 | 綜合線條 | 自訂 | 組 | 50 | 10 | 每天 | 隨意畫各種交錯的直線與曲線，隨意選區擷取後臨摹，要畫精準。 |
| 2 | 基本形狀 | 自訂 | 頁 | 1 | 10 | 每天 | 正方形、圓形、方形、橢圓形、菱形，由小到大。 |
| 3 | 用線條概括 | 自訂 | 張 | 20 | 10 | 每天 | 隨機找圖，旁邊擴展等大的空白畫布。先畫最大分割的紅線（不超過 3 條），再畫次要分割的藍線。 |
| 4 | Static & Dynamic Forms | CAS | 頁 | 1 | 60 | daily | |
| 4 | 幾何概括+翻轉 | 自訂 | 張 | 10 | 30 | 每天 | 隨機找有獨立物體的圖，用基本幾何（可以變形，例如橢圓）概括物體的結構，物體本身和位置都要準確。再把物體裝進盒子，根據概括畫出翻轉後的版本，每個概括 2 個。 |
| 5 | 1 Point Perspective | PAS | 頁 | 1 | 120 | Daily / Weekly | |
| 5 | 2 Point Perspective | PAS | 頁 | 1 | 120 | Daily / Weekly | |
| 5 | 3 Point Perspective | PAS | 頁 | 1 | 120 | Daily / Weekly | |
| 5 | Stacking Perspective | PAS | 頁 | 1 | 120 | Daily / Weekly | |
| 6 | Proportions | CAS | 頁 | 1 | 60 | daily until memorized | |
| 6 | Character Forms | CAS | 頁 | 1 | 30 | daily | |
| 6 | Body Proportion | MAS | 頁 | 1 | 60 | weekly until learned | |
| 6 | Head & Body Sketches | MAS | 頁 | 1 | 120 | once off | |
| 7 | 骨架五步 | 自訂 | 張 | 1 | 10 | 每天 | 1. 從 Line of Action 取參考。2. 畫動態線。3. 火柴人。4. 幾何人。5. 人偶。 |
| 8 | Line of Action 30 秒 | 自訂 | 張 | 20 | 10 | 每天 | 30 秒一張，只抓動態線和大形。 |
| 8 | Line of Action 1 分鐘 | 自訂 | 張 | 8 | 10 | 每天 | 1 分鐘一張，動態線加上簡單的形體。 |
| 8 | Life Gestures | CAS | 頁 | 1 | 5 | daily / forever if possible | |
| 9 | Dynamic Shape Gestures | CAS | 頁 | 1 | 20 | daily for 3 weeks | |
| 9 | Dynamic Form Gestures | CAS | 頁 | 1 | 40 | daily for 3 weeks | |
| 10 | Camera Angle | PAS | 頁 | 1 | 120 | Daily / Weekly | |
| 10 | Cone of Vision | PAS | 頁 | 1 | 120 | Weekly | |
| 10 | Spatial Zones | PAS | 頁 | 1 | 60 | once off | |
| 11 | Full Form Bodies | CAS | 頁 | 1 | 60 | daily / every 2nd day | |
| 12 | Anatomical Gestures | CAS | 頁 | 1 | 40 | daily for 3 weeks | |
| 13 | Facial Features | CAS | 頁 | 1 | 30 | daily | |
| 13 | Heads & Features | CAS | 頁 | 1 | 120 | daily / every 2nd day | |
| 13 | Head Proportion | MAS | 頁 | 1 | 60 | weekly until learned | |
| 13 | Eye Designs | MAS | 頁 | 1 | 120 | weekly | |
| 13 | Head Drawings | MAS | 頁 | 1 | 60 | daily | |
| 13 | Age Variation | MAS | 頁 | 1 | 60 | weekly / once off | |
| 14 | Facial Expression Sheets | CAS | 頁 | 1 | 90 | twice weekly | |
| 14 | Observational Studies | CAS | 頁 | 1 | 120 | once / month | |
| 14 | Front View Face | MAS | 頁 | 1 | 60 | Daily / Weekly | |
| 14 | Rotated View Face | MAS | 頁 | 1 | 120 | Daily / Weekly | |
| 15 | Hands Proportion | MAS | 頁 | 1 | 60 | weekly until learned | |
| 16 | Hair Design Sheets | CAS | 頁 | 1 | 120 | twice weekly | |
| 16 | Hair Design | MAS | 頁 | 1 | 60 | Daily / Weekly | |
| 17 | Clothing Fold Types | CAS | 頁 | 1 | 120 | one time | |
| 17 | Character w/ Clothing | MAS | 張 | 1 | 120 | once off | |
| 18 | 4 Stage Workflow Drawings | CAS | 張 | 1 | 120 | daily / every 2nd day | |
| 18 | 2 Stage Workflow Drawings | CAS | 張 | 1 | 120 | daily / every 2nd day | |
| 18 | Manga Clean-Up | MAS | 張 | 1 | 180 | once off | |
| 18 | Final Drawing | MAS | 張 | 1 | 240 | once off | |
| 18 | Character Drawing | CAS | 張 | 1 | 180 | | |
| 19 | Finding Center and Duplicating Planes | PAS | 頁 | 1 | 120 | Daily / Weekly | |
| 19 | Scaling In Perspective | PAS | 頁 | 1 | 120 | Daily / Weekly | |
| 19 | Drawing Ellipses in Perspective | PAS | 頁 | 1 | 120 | Daily / Weekly | |
| 19 | Complete Environment Piece | PAS | 張 | 1 | | Weekly / Self-Directed | |
| 20 | Combining Theories | CAS | 張 | 1 | 240 | one time | |
| 20 | Character Busts | CAS | 張 | 1 | 240 | one time | |
| 21 | 色彩複製 | 自訂 | 個 | 20 | 10 | 每天 | 隨機找圖，閉眼用吸管隨機取幾個顏色，刷到空白畫布上，再試著複製：先色相，再明度，要準確。 |
| 22 | 週末粗稿 | 自訂 | 張 | 1 | 30 | 每週 | 畫任何想畫的角色，用目前等級的能力，不求精修。 |
| 22 | Personal Character Piece | CAS | 張 | 1 | 180 | weekly | |
| 22 | Character Fanart Piece | CAS | 張 | 1 | 180 | weekly | |
| 23 | Visual Library Development | CAS | 主題 | 1 | 60 | weekly | |
| 24 | Comparative Drawing | CAS | 張 | 1 | 180 | once off | |

Exercise 7 and 8 carry one resource each: `Line of Action`,
`https://line-of-action.com/`. Seeded exercises have no topics: the owner
tags them.

**A range takes its lower bound** in `suggested_minutes` (`1-3 hr` → 60,
`5-60 m` → 5), with the sheet's own wording in `frequency`; a blank there
stays NULL.

## API

| Method | Path | |
| --- | --- | --- |
| GET | `/api/exercises` | `?q=&stage_id=&topic_id=&no_stage=true`; summaries with stage `{id, number, display_name}`, topics, drill count, record count, total minutes |
| GET | `/api/exercises/{id}` | with drills (full), resources, aliases, topics |
| POST/PATCH/DELETE | `/api/exercises[/{id}]` | delete 409 `{detail, drills, records}` |
| GET | `/api/drills/{id}` | |
| POST/PATCH/DELETE | `/api/drills[/{id}]` | delete 409 `{detail, records}` |
| GET | `/api/records` | `?from=&to=&kind=&exercise_id=&drill_id=&stage_id=&goal_id=`; newest first; `exercise_id` matches records naming it directly or through a drill |
| GET | `/api/records/{id}` | |
| POST/PATCH/DELETE | `/api/records[/{id}]` | |
| GET | `/api/records/summary` | `?from=&to=`: per day `{date, minutes, records}` |

## Frontend

Nav: 路線圖 · 練習 · 紀錄 · 筆記 · 選項.

| Route | Page |
| --- | --- |
| `/exercises` | grouped by stage in roadmap order, then 不分階段; search and topic filter |
| `/exercises/:id` | description, resources, topics, remark; drills as cards (source, unit × target, minutes, frequency, instructions, links) each with 記錄 → `/records/new?drill=`; the exercise's records and total minutes |
| `/exercises/new`, `/exercises/:id/edit` | form |
| `/drills/new?exercise=`, `/drills/:id/edit` | form |
| `/records` | grouped by date, newest first, each day's total minutes; this week's total; filters kind / exercise |
| `/records/new`, `/records/:id/edit` | date (today), location (the last record's), duration, drill-or-exercise picker, kind, stage-or-goal when test, method (with descriptions), tool (Clip Studio Paint by default), reference links, notes |

The stage page gains its exercises and its test records.

The roadmap's stage page gains two lists: the stage's exercises, and its test
records (newest first).

## Rules worth testing

- A drill and an exercise on one record is a 422; so is a `test` record with
  no stage and no goal, or with both, and a stage or goal on a non-test record.
- Option fields take only their own category (`source`, `location`, `tool`,
  `method`); the refusal tests create an option of another category first.
- Deleting a drill, exercise, stage or goal named by records is a 409 stating
  the count; the refusal test creates the record first, and its mirror deletes
  once the record is gone. An exercise with drills is a 409 as well.
- `GET /api/records?exercise_id=` returns records naming the exercise directly
  **and** through its drills.
- Deleting a `stage` named by an exercise sets the exercise's stage to none.
- The summary sums minutes per day, counting a record with no duration as a
  record but zero minutes.
- The seed: 24 exercises, 57 drills, 3 new categories with their values; the
  from-zero test checks counts and a few verbatim strings, and the downgrade
  round trip.

## Out of scope

Images on records (designed later: Google Drive or Google Photos), the timer
(the next module creates records), schedule, charts beyond the per-day
summary.
