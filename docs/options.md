# Options and vocabularies

Every dropdown, category and tag draws from a fixed list somewhere. This page
lists them all and says where each lives. As in `media`, one question decides
the tier: **does code branch on the exact value?**

| Tier | Lives in | Changed by | Here |
| --- | --- | --- | --- |
| 1 | Python constants in `app/constants.py` | a code change | `Visibility`, the goal and stage statuses, and the option **categories** |
| 2 | `system_option` rows | the Options page (`/options`) | every value below |
| 3 | entity tables | their own module | none yet |

## Tier 1

| Name | Values | Used by |
| --- | --- | --- |
| `Visibility` | `private`, `unlisted`, `public` | `note.visibility` (reserved; nothing reads it yet) |
| `GoalStatus` | `planned`, `active`, `achieved` (計畫中, 進行中, 已達成) | `goal.status` |
| `StageStatus` | `not_started`, `in_progress`, `passed` (未開始, 進行中, 已通過) | `stage.status` |
| `RecordKind` | `practice`, `piece`, `test` (練習, 作品, 測驗) | `record.kind`; a test names a stage or a goal |
| `TimerMode` | `stopwatch`, `countdown` | `active_timer.mode` |
| `TimerState` | `running`, `paused`, `stopped` | derived for responses, never stored |
| `OPTION_CATEGORIES` | `note_category`, `topic`, `method`, `source`, `location`, `tool`, `reference_group` | `system_option.category`, and the Options page's section order |

**Categories are registered, not typed.** Each has a key, a label and a
description, and the Options page heads each section with the label and the
description before listing its values. `ck_system_option_category` is built
from the registry, so **adding a category is a code change plus a migration
that replaces the check** — a key the code registers but the database refuses
is an insert that fails at runtime.

## Tier 2: system options

Edited on the Options page: value, description, remark and order. A value's
**description** is what it means, shown wherever it is picked; its **remark**
is a note to yourself, shown only on the Options page.

| Category | Label | Read by | Seeded values |
| --- | --- | --- | --- |
| `note_category` | 筆記分類 | `note.category_id` (single, optional) | 名詞, 知識, 小技巧, 建議 |
| `topic` | 主題 | `note_topic`, `exercise_topic` (several each) | 線條, 形狀, 透視, 比例, 人體, 動態, 構圖, 光影, 色彩, 特效 |
| `method` | 方法 | `record.method_id` | 臨摹, 重現, 描寫, 速寫, 同人創作, 原創創作, 隨便畫 |
| `source` | 來源 | `drill.source_id` | Character Art School, Character Art School: Coloring, Manga Art School, Perspective Art School, 自訂, 其他 |
| `location` | 地點 | `record.location_id` | 台灣・家, 美國・家 |
| `tool` | 工具 | `record.tool_id` | Clip Studio Paint, Procreate, 紙筆 |
| `reference_group` | 參考分組 | `reference_group` (several per reference) | none — the owner creates the groups |

The seeded `method` values carry these descriptions:

| Value | Description |
| --- | --- |
| 臨摹 | 直接在參考圖上方描繪，盡量完整還原。（很少使用） |
| 重現 | 不疊在參考圖上，看著參考圖盡量完整還原整張圖，例如動畫截圖。屬於描寫的一種。 |
| 描寫 | 看著參考圖畫，不疊在參考圖上。不要求完整還原。 |
| 速寫 | 限時快速畫，抓動態和大形，不追求細節。 |
| 同人創作 | 以既有角色或作品為題材的創作：構圖和姿勢是自己的，對象是別人的。 |
| 原創創作 | 原創題材，例如自己的原創角色。可以使用參考資料。 |
| 隨便畫 | 沒有特定目標，想畫什麼就畫什麼。 |

These are the seed, not the truth: the Options page edits them, and this table
says what a fresh database starts with.

## Rules

- **Links are by id.** Renaming a value changes it everywhere at once.
- **A field takes only its own category's values.** Checked in the service;
  the wrong category is a 422.
- **A value's category never changes** once created.
- **Deleting a value in use states the cost first.** The page shows how many
  references it removes; the delete is refused if that count has changed by
  the time it arrives. Then tag links — topics, reference groups — are removed
  and single references set to none.
- A category's values are unique after trimming, ignoring case.
