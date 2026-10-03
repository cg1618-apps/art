# Timer — design

Module 6 of `docs/notes/decisions.md`, "Structure". Working scaffolding;
deleted when the module lands.

`CLAUDE.md` names the stopwatch as the one feature on the platform that might
want a different shape — live session state rather than a catalogue. This is
that decision, made deliberately: **same stack, with the running timer's state
held by the server and the ticking done by the browser.** Recorded in
`decisions.md` when it lands.

## What the owner agreed

- **The server holds the running timer**, so a refresh, a closed tab or a
  sleeping laptop loses nothing, and the timer shows on any device.
- **Stopwatch and countdown.** No interval mode: Line of Action already times
  30s × 20; this times the session.
- **A countdown that reaches zero keeps going as overtime** (`+0:42`) and plays
  a sound, since Clip Studio Paint, not the browser, is in front.
- **Pause and resume.**
- **Optionally attached to a drill or an exercise** from the start; a drill card
  gets 開始計時 beside 記錄.
- **Stopping opens the record form prefilled** — duration rounded to the
  nearest minute (at least 1), the drill or exercise, the date the timer
  started, the usual defaults — and saving it creates the record and ends the
  timer. 捨棄 throws the session away.
- **One timer per record.** No "next item" chaining.
- **Visible everywhere**: a compact timer in the top bar of every page while one
  exists, a `/timer` page with large digits, and the remaining or elapsed time
  in the tab title.
- **Only one timer at a time.**
- **A timer stopped after more than 3 hours** asks for the duration to be
  checked before it becomes a record.
- **The default countdown is 10 minutes Monday to Friday and 30 on Saturday
  and Sunday** — the owner's schedule, held as a frontend constant until the
  Schedule module owns it.

## Table: `active_timer`

At most one row (`uq_active_timer_single`, a unique index on `((true))`).

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| `id` | integer | no | |
| `mode` | text | no | `stopwatch` / `countdown` (`TimerMode`, Tier 1) |
| `target_seconds` | integer | yes | required for a countdown, NULL for a stopwatch (`ck_active_timer_target`), ≥ 1 |
| `started_at` | timestamptz | no | when it was first started |
| `running_since` | timestamptz | yes | NULL while paused or stopped |
| `elapsed_seconds` | integer | no | counted before `running_since`; default 0 |
| `stopped_at` | timestamptz | yes | set by stop; a stopped timer waits for its record |
| `drill_id` | integer | yes | → `drill`, `SET NULL` |
| `exercise_id` | integer | yes | → `exercise`, `SET NULL`; never both (`ck_active_timer_one_activity`) |
| timestamps | | | |

- `ck_active_timer_state`: not both `running_since` and `stopped_at`.
- State is derived: `running` (running_since set), `paused` (neither),
  `stopped` (stopped_at set).
- **Every time comes from the database clock** (`now()`), never the client's:
  two devices must agree on one timer.
- `SET NULL` on the activity, not RESTRICT: a running timer is not history,
  and deleting the drill should not be blocked by it.

## API

```text
TimerResponse { id, mode, target_seconds, state, started_at, running_since,
                elapsed_seconds, stopped_at, now,
                activity: { exercise: {id, display_name}, drill: {id, display_name} | null } | null }
```

`now` is the server's clock at response time; the browser computes the live
figure as `elapsed_seconds + (now - running_since)` against its own clock
offset by `now`, so a skewed laptop clock does not skew the timer.

| Method | Path | |
| --- | --- | --- |
| GET | `/api/timer` | 200 with the timer, or 200 with `null` |
| POST | `/api/timer` | `{ mode, target_seconds?, drill_id?, exercise_id? }` → 201, running. 409 when one exists |
| PATCH | `/api/timer` | `{ target_seconds?, drill_id?, exercise_id? }` while it exists |
| POST | `/api/timer/pause` | running → paused; anything else 409 |
| POST | `/api/timer/resume` | paused → running; anything else 409 |
| POST | `/api/timer/stop` | running or paused → stopped; returns the timer with final `elapsed_seconds` |
| POST | `/api/timer/record` | body is a record write (as `POST /api/records`); creates the record **and** deletes the timer in one transaction; 201 with the record. Only for a stopped timer, else 409 |
| DELETE | `/api/timer` | 捨棄: deletes it, 204 |

404 when there is no timer for PATCH / pause / resume / stop / record /
DELETE. Activity ids follow the record rules (drill or exercise, not both;
must exist).

## Frontend

- `TimerProvider` (context) over `GET /api/timer`, refetched on focus and every
  30 s, ticking every second locally; exposes the live seconds, remaining for a
  countdown, and the actions.
- **Top bar**: while a timer exists, a compact chip — activity name, `mm:ss` (or
  `+mm:ss` in overtime, coloured), pause/resume — linking to `/timer`.
- **`/timer`**: with no timer, a start form — stopwatch / countdown toggle,
  presets 10 and 30 minutes plus a custom number of minutes (default from the
  day of week), and an optional exercise-then-drill picker (`?drill=` or
  `?exercise=` preselects). With a timer: large digits, activity, pause /
  resume, 停止, 捨棄 (confirm dialog).
- **At zero** a countdown plays a short tone (Web Audio, no asset) once, and
  keeps counting.
- **Tab title**: `▶ 7:42 · art` / `⏸ …` / `+0:42 …` while a timer exists.
- **停止** → `POST /api/timer/stop`, then `/records/new?from=timer`: the record
  form prefilled with duration (round to nearest minute, min 1), activity,
  date (the local date of `started_at`) and the usual defaults; its save posts
  to `/api/timer/record`. Leaving the form keeps the timer stopped — the top bar
  chip says 待記錄 and leads back to the form. If elapsed > 3 hours the form
  shows a warning beside the duration.
- **Drill card** 開始計時: starts a countdown with the day's default and the
  drill attached, then goes to `/timer`; if a timer already exists, it just
  goes to `/timer`.
- Nav: 計時 between 紀錄 and 筆記.

## Tests

Backend: single-timer refusal (create one first), state transitions and their
409s, pause/resume accumulate elapsed by the database clock (assert ranges,
not exact values), stop freezes it, record-from-timer creates the record and
removes the timer atomically (a refused record write leaves the timer intact),
countdown requires a target and stopwatch refuses one, activity rules, the
singleton index at the database level, deleting a drill nulls the timer's
activity. Frontend: the live figure from `now` offset, overtime formatting,
the tone fires once at zero, the start form defaults by weekday, stop leads to
a prefilled record form whose save hits `/api/timer/record`, the top bar chip.

## Out of scope

Chaining items, interval mode, notifications outside the page, the Schedule
module (which will replace the weekday constant).
