# Goals + Roadmap — design

Modules 2 and 3 of `docs/notes/decisions.md`, "Structure", built together:
a goal is a level, a level is nothing without its stages, and neither page is
useful alone. Working scaffolding; deleted when the module lands.

The content — six levels, sixteen stages, a test for each — was agreed with the
owner before this design, and ships as seed data (below).

## What the owner agreed

- **Levels, named for what you can draw**, not short / mid / long term: at 10
  minutes a day nobody can promise a duration, and a level is passed by its
  test, not by a date.
- **Every level and every stage closes with a test**: a piece you redraw over
  time. The test is how "progress" gets a picture instead of only hours.
- Values: perspective and proportion before detail; "rough but good" beats
  "it looks weird". Anime/manga style. Clip Studio Paint, screenless tablet.

## Tables

### `goal` — a level

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | integer | no | |
| `code` | text | no | `L0` … `L5`; unique (`uq_goal_code`), trimmed |
| `name_cn`, `name_en`, `name_alt` | text | yes | at least one (`ck_goal_has_a_name`) |
| `position` | integer | no | order on the roadmap |
| `description` | text | yes | "done when you can …" |
| `test` | text | yes | the test piece |
| `status` | text | no | `planned` / `active` / `achieved` (Tier 1, `GoalStatus`), default `planned` |
| `achieved_on` | date | yes | only when `achieved` (`ck_goal_achieved_on_iff_achieved`: set ⇒ achieved; achieved may leave it NULL) |
| `remark` | text | yes | |
| timestamps | | | |

### `stage`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | integer | no | |
| `goal_id` | integer | no | → `goal`, `RESTRICT`, indexed |
| `position` | integer | no | order inside its goal |
| `name_cn`, `name_en`, `name_alt` | text | yes | at least one |
| `description` | text | yes | the focus: what is practised |
| `test` | text | yes | the stage's test |
| `status` | text | no | `not_started` / `in_progress` / `passed` (`StageStatus`), default `not_started` |
| `passed_on` | date | yes | only when `passed`, same rule as `achieved_on` |
| `remark` | text | yes | |
| timestamps | | | |

`stage_resource`: `food`'s `tbd_link` shape, exactly as `note_resource` —
`id`, `stage_id` (CASCADE), `position`, `name`, `url`, btrim CHECK. For the
lectures to rewatch at the start of a stage.

**Stage number** is derived, never stored: stages ordered by (goal position,
stage position, id), numbered from 0. The roadmap shows "Stage 3"; moving a
stage renumbers everything after it for free.

**Deleting a goal that still has stages is a 409** naming the count — RESTRICT,
because a goal's stages are the roadmap and losing them by deleting a level
header would be the wrong surprise. Deleting a stage cascades its resources;
later modules decide what their own references to a stage do (exercises: SET
NULL; test records: RESTRICT).

**Status is set by hand.** Nothing derives a goal's status from its stages, so
the owner can pass a level on its test before every stage is ticked, which is
how tests are meant to work.

## Seed (migration, raw SQL, idempotent on `goal.code` / stage name)

Goals (`code`, `name_cn`, `name_en`, description / test). L0 seeds `active`,
the rest `planned`; every stage `not_started`.

| code | 中文 | English | description | test |
| --- | --- | --- | --- | --- |
| L0 | 基礎 | Foundations | 能穩定地畫出線條與基本形狀，並把方塊、圓柱、球體放進透視空間。 | 一頁穩定的線條與橢圓，加上 20 個隨機角度、看起來都立體的方塊。 |
| L1 | 人體 | Figure | 能憑想像畫出有動態的全身人體，在平視、俯視、仰視下比例都正確。頭部用簡單形體即可。 | 同一個姿勢以平視、俯視、仰視各畫一次的人偶。 |
| L2 | 角色 | Character | 把人體變成具體的動漫角色：臉、表情、手、頭髮、衣服、小配件。 | 從 Drawing List 選一個角色，以動作姿勢、三個角度各畫一次。 |
| L3 | 場景 | Scene | 把角色放進透視正確的背景，仍不上色：同一條地平線、合理的比例、腳踩在地上。 | 角色在房間或街道中的線稿，兩點透視。 |
| L4 | 上色 | Colour | 先用灰階明度、再用顏色為角色上色，光源明確。 | 簡單背景的上色角色。 |
| L5 | 插畫 | Illustration | 完成有背景的彩色插畫，包含動物、奇幻生物與特效。 | 從縮圖到完稿的一張完整作品。 |

Stages, in order (goal, 中文, English, description, test):

| # | goal | 中文 | English | description | test |
| --- | --- | --- | --- | --- | --- |
| 0 | L0 | Clip Studio Paint 設定 | Clip Studio Paint setup | 筆刷、穩定化、快捷鍵、翻轉畫布快捷鍵、透視尺，以及之後用來檢查比例與鏡頭角度的 3D 素描人偶。 | 2 分鐘內擺好 3D 人偶的姿勢並設定鏡頭角度。 |
| 1 | L0 | 線條與形狀 | Lines and shapes | 只有 2D：直線、曲線、弧線、波浪線、鋸齒線、圓形、橢圓、方形、菱形。用手肘和肩膀畫，不用手腕。 | 一頁穩定、不抖的線條與橢圓。 |
| 2 | L0 | 空間中的形體 | Form in space | 方塊、圓柱、球體在一點、兩點、三點透視中，自由旋轉。 | 20 個隨機角度、看起來都立體的方塊，以及橢圓正確的圓柱。 |
| 3 | L1 | 比例 | Proportion | 以頭身為單位的人體，用基本形體組成人偶。 | 憑記憶畫出正面、側面、¾ 的人偶，疊在 3D 人偶上誤差在半個頭以內。 |
| 4 | L1 | 動態到人偶 | Gesture to mannequin | 動態線，然後是動態形狀與動態形體。 | 憑想像畫一個動態，轉成人偶後仍保有動感。 |
| 5 | L1 | 透視中的人體 | Figure in perspective | 鏡頭角度、視錐、透視縮短。解決「看起來怪怪的」的階段。 | 同一個姿勢以平視、俯視、仰視各畫一次。 |
| 6 | L2 | 主要肌肉量塊 | Major muscle masses | 胸廓、骨盆、肩帶與大肌群，疊在人偶上，只到量塊層級。 | 在三個動態人偶上畫出主要量塊。 |
| 7 | L2 | 頭部、五官、表情 | Head, face, expression | 任何角度的頭部、五官位置、動漫風格化與表情。 | 同一個角色，三個角度、六種表情。 |
| 8 | L2 | 手與腳 | Hands and feet | 用方塊與圓柱組成手和腳，再加上姿勢。 | 一頁不同姿勢的手與腳。 |
| 9 | L2 | 完稿：頭髮、衣服、配件 | Finishing | 頭髮的大形、衣褶、配件、線條粗細、四階段流程。 | L2 的測驗作品。 |
| 10 | L3 | 環境透視 | Environment perspective | 找中心與複製平面、透視中的縮放與橢圓、空間分區。 | 兩點透視的房間，家具都對準消失點。 |
| 11 | L3 | 構圖與角色入景 | Composition and character in scene | 縮圖、三分法、引導線，把角色放進場景。 | 三張縮圖，選一張完成線稿。 |
| 12 | L4 | 明度與光影 | Value and light | 只用灰階：明度、單一光源、陰影。 | 單一光源的灰階角色。 |
| 13 | L4 | 色彩 | Colour | 色相、明度、彩度，色彩和諧與上色流程。 | L4 的測驗作品。 |
| 14 | L5 | 完整插畫與生物 | Full pieces and creatures | 大氣透視、完整流程，以及用基本形體組成動物與奇幻生物。 | 一張有背景的完整作品。 |
| 15 | L5 | 特效 | Effects | 火焰、閃電、魔法、發光、煙霧：形狀、由亮到暗的漸層，以及 Clip Studio Paint 的發光與相加類圖層。 | 一張有火球的角色插畫。 |

These are the seed, not the truth: the pages edit them.

## API

Errors and PATCH semantics as `docs/api.md`.

| Method | Path | |
| --- | --- | --- |
| GET | `/api/goals` | every goal in position order, each with its stages (summaries, numbered) |
| GET | `/api/goals/{id}` | |
| POST | `/api/goals` | 201; no `position` puts it last |
| PATCH | `/api/goals/{id}` | |
| DELETE | `/api/goals/{id}` | 204; 409 `{detail, stages: n}` when it has stages |
| GET | `/api/stages/{id}` | with its goal (`{id, code, display_name}`), number and resources |
| POST | `/api/stages` | 201; `goal_id` required; no `position` puts it last in that goal |
| PATCH | `/api/stages/{id}` | may change `goal_id` (moves it; lands last unless `position` sent) |
| DELETE | `/api/stages/{id}` | 204 |

```text
GoalResponse   { id, code, display_name, name_cn, name_en, name_alt, position,
                 description, test, status, achieved_on, remark, stages: [StageSummary] }
StageSummary   { id, number, display_name, name_cn, name_en, name_alt, position,
                 description, test, status, passed_on }
StageResponse  StageSummary + { goal: {id, code, display_name}, remark,
                 resources: [{id, name, url}] }
GoalWrite      { code, name_cn?, name_en?, name_alt?, position?, description?, test?,
                 status?, achieved_on?, remark? }
StageWrite     { goal_id, name_cn?, name_en?, name_alt?, position?, description?, test?,
                 status?, passed_on?, remark?, resources?: [{name?, url}] }
```

Setting `status` away from `achieved` / `passed` clears the date; sending a
date with any other status is a 422.

## Frontend

Nav becomes 路線圖 · 筆記 · 選項, and `/` redirects to `/roadmap`.

| Route | Page |
| --- | --- |
| `/roadmap` | every level in order: code, name, status, description, test; under it its stages as rows — number, name, status, test. The **current stage** (the first not passed, in order) is highlighted. A stage's status changes from the row (a small select), passing sets today's date |
| `/roadmap/goals/new`, `/roadmap/goals/:id/edit` | goal form |
| `/roadmap/stages/:id` | stage detail: description, test, resources, remark, status |
| `/roadmap/stages/new?goal=:id`, `/roadmap/stages/:id/edit` | stage form, resources as name + link rows |

Reordering is by `position` fields on the forms and ↑/↓ on the roadmap rows.

## Tests

Backend: CRUD, name required, `code` unique, date-iff-status rules with
mirrors, RESTRICT on a goal with stages (the refusal test creates a stage so
it can bite), numbering across goals and after a move, the seed (six goals,
sixteen stages, numbering 0–15) in the from-zero migration test. Frontend: the
roadmap renders levels and stages with the current stage marked; a status
change sends the PATCH.

## Out of scope

Linking exercises (the next module adds `exercise.stage_id`) and test records
(the next module adds `record.stage_id`).
