// Frontend: the timer - its live figure, how it is written, the day's default
// countdown, and the record a stopped timer becomes.
//
// The server holds the timer (GET /api/timer); the browser only ticks. Every
// read of a TimerResponse field goes through here, so a field the API renames
// is a one-line fix.
//
// The live figure is `elapsed_seconds + (server now - running_since)`, where
// "server now" is the browser's clock shifted by the offset measured when the
// response arrived (`now` minus the moment it was received). A laptop whose
// clock is minutes off therefore still agrees with the phone.
import { localToday, parseTarget, targetValue } from './roadmap'
import { emptyRecordForm, UNCHOSEN } from './records'
import { integerOrNull, keyed } from './rowList'

export const STOPWATCH = 'stopwatch'
export const COUNTDOWN = 'countdown'

export const TIMER_MODES = [
  { value: COUNTDOWN, label: '倒數' },
  { value: STOPWATCH, label: '碼錶' },
]

export const RUNNING = 'running'
export const PAUSED = 'paused'
export const STOPPED = 'stopped'

/** The countdown presets on the start form, in minutes. */
export const COUNTDOWN_PRESETS = [10, 30]

/**
 * The owner's schedule: 10 minutes on a weekday, 30 at the weekend. A
 * frontend constant until the Schedule module owns the schedule and replaces
 * this.
 */
export const DEFAULT_COUNTDOWN_MINUTES = { weekday: 10, weekend: 30 }

/** A timer stopped after longer than this asks for its duration to be checked. */
export const LONG_TIMER_SECONDS = 3 * 60 * 60

/** The default countdown for `date`'s day of the week, in minutes. */
export function defaultCountdownMinutes(date = new Date()) {
  const day = date.getDay()
  return day === 0 || day === 6 ? DEFAULT_COUNTDOWN_MINUTES.weekend : DEFAULT_COUNTDOWN_MINUTES.weekday
}

// ---------------------------------------------------------------- reading

/**
 * GET /api/timer's body as a timer, or null. The endpoint answers `null` when
 * there is none; anything that is not a timer counts as none.
 */
export function asTimer(body) {
  return body && typeof body === 'object' && !Array.isArray(body) && body.state ? body : null
}

export const isRunning = (timer) => timer?.state === RUNNING
export const isPaused = (timer) => timer?.state === PAUSED
export const isStopped = (timer) => timer?.state === STOPPED
export const isCountdown = (timer) => timer?.mode === COUNTDOWN

/** The exercise the timer is attached to, directly or through its drill - `{ id, display_name }` - or null. */
export function timerExercise(timer) {
  return timer?.activity?.exercise ?? null
}

/** The drill the timer is attached to, `{ id, display_name }`, or null. */
export function timerDrill(timer) {
  return timer?.activity?.drill ?? null
}

/** What the timer is timing, in one name: the drill's, else the exercise's, else null. */
export function timerActivityName(timer) {
  return (timerDrill(timer) ?? timerExercise(timer))?.display_name ?? null
}

/**
 * Server clock minus browser clock, in ms, given the response and the
 * browser's time (ms) when it arrived.
 */
export function clockOffset(timer, receivedAt) {
  if (!timer?.now || receivedAt == null) return 0
  const serverNow = Date.parse(timer.now)
  return Number.isNaN(serverNow) ? 0 : serverNow - receivedAt
}

/**
 * The timer's elapsed seconds at browser time `clientNow` (ms), with the
 * server's clock `offset` ms ahead of the browser's. Paused and stopped
 * timers are what the server counted.
 */
export function liveSeconds(timer, clientNow, offset = 0) {
  if (!timer) return 0
  const counted = timer.elapsed_seconds ?? 0
  if (!isRunning(timer) || !timer.running_since) return counted
  const since = Date.parse(timer.running_since)
  if (Number.isNaN(since)) return counted
  return counted + Math.max(0, Math.floor((clientNow + offset - since) / 1000))
}

/** Seconds left on a countdown - negative in overtime - or null for a stopwatch. */
export function remainingSeconds(timer, seconds) {
  if (!isCountdown(timer) || timer.target_seconds == null) return null
  return timer.target_seconds - seconds
}

/** Whether a countdown has reached zero. */
export function isOvertime(timer, seconds) {
  const remaining = remainingSeconds(timer, seconds)
  return remaining !== null && remaining < 0
}

// ------------------------------------------------------------- formatting

const pad = (n) => String(n).padStart(2, '0')

/** Seconds as a clock: "7:42", "0:05", "1:02:09". */
export function formatClock(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return h ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`
}

/**
 * What the timer shows at `seconds` elapsed: the time left on a countdown,
 * "+0:42" once it is past zero, the elapsed time on a stopwatch.
 */
export function timerClock(timer, seconds) {
  const remaining = remainingSeconds(timer, seconds)
  if (remaining === null) return formatClock(seconds)
  return remaining < 0 ? `+${formatClock(-remaining)}` : formatClock(remaining)
}

/** The tab title while a timer exists: "▶ 7:42 · art", "⏸ 7:42 · art", "+0:42 · art", "待記錄 · art". */
export function timerTitle(timer, seconds, base = 'art') {
  if (isStopped(timer)) return `待記錄 · ${base}`
  const clock = timerClock(timer, seconds)
  if (isOvertime(timer, seconds)) return `${isPaused(timer) ? '⏸ ' : ''}${clock} · ${base}`
  return `${isPaused(timer) ? '⏸' : '▶'} ${clock} · ${base}`
}

// ------------------------------------------------------------------ writes

/**
 * The start form as POST /api/timer's body. A countdown carries its target, a
 * stopwatch none; the activity is a drill or an exercise, never both, as a
 * record's.
 */
export function startPayload({ mode, minutes, exerciseId = '', drillId = '' }) {
  const body = { mode }
  if (mode === COUNTDOWN) body.target_seconds = Math.round(Number(minutes) * 60)
  if (drillId !== '' && drillId != null) body.drill_id = Number(drillId)
  else if (exerciseId !== '' && exerciseId != null) body.exercise_id = Number(exerciseId)
  return body
}

/** Whether `minutes` (as typed) is a countdown the server will accept: a whole number, at least 1. */
export function validMinutes(minutes) {
  const value = Number(minutes)
  return minutes !== '' && Number.isInteger(value) && value >= 1
}

// --------------------------------------------------------- the record form

/** Seconds as a record's minutes: to the nearest minute, at least 1. */
export function roundToMinutes(seconds) {
  return Math.max(1, Math.round((seconds ?? 0) / 60))
}

/** Whether a stopped timer ran long enough that its duration should be checked. */
export function isLongTimer(timer) {
  return (timer?.elapsed_seconds ?? 0) > LONG_TIMER_SECONDS
}

/** The timer's record draft, `{ kind, stage_id, … }` with only the keys the owner chose, or null. */
export function timerDraft(timer) {
  return timer?.draft ?? null
}

/**
 * The record form a timer opens with: its minutes, its drill or exercise, the
 * local date it started, its record draft, and the usual defaults for what
 * the draft leaves out.
 */
export function timerRecordForm(timer) {
  const exercise = timerExercise(timer)
  const drill = timerDrill(timer)
  const started = timer.started_at ? new Date(timer.started_at) : new Date()
  const form = {
    ...emptyRecordForm({
      today: localToday(started),
      exercise: exercise ? String(exercise.id) : null,
      drill: drill ? String(drill.id) : null,
    }),
    duration_minutes: String(roundToMinutes(timer.elapsed_seconds)),
  }
  return withDraft(form, timerDraft(timer))
}

const has = (draft, key) => Object.prototype.hasOwnProperty.call(draft, key)

/**
 * `form` with a stored draft's keys applied. A key the draft does not carry
 * leaves the form's value - for the location and the tool, UNCHOSEN, so their
 * defaults still apply.
 */
export function withDraft(form, draft) {
  if (!draft) return form
  const next = { ...form }
  if (has(draft, 'kind') && draft.kind) next.kind = draft.kind
  if (draft.goal_id != null) next.target = targetValue('goal', draft.goal_id)
  else if (draft.stage_id != null) next.target = targetValue('stage', draft.stage_id)
  for (const field of ['method_id', 'location_id', 'tool_id']) {
    if (has(draft, field)) next[field] = draft[field]
  }
  if (Array.isArray(draft.references)) {
    next.references = draft.references.map((row) => keyed({ name: row.name ?? '', url: row.url ?? '' }))
  }
  if (has(draft, 'notes')) next.notes = draft.notes ?? ''
  return next
}

/**
 * The record form as PATCH /api/timer's body: the activity, and the rest as
 * the draft. The activity is sent as a record's is - with a drill the
 * exercise is null. The draft keeps the form as typed (a reference row with
 * no link yet, a test with no target yet) and leaves out a location or tool
 * still UNCHOSEN, so it is not pinned to today's default. The target is kept
 * whatever the kind, so switching away from 測驗 and back does not lose it;
 * the record's own payload drops it unless the kind is a test.
 */
export function draftPayload(form) {
  const drillId = integerOrNull(form.drill_id)
  const draft = {
    kind: form.kind,
    ...parseTarget(form.target),
    method_id: form.method_id,
  }
  if (form.location_id !== UNCHOSEN) draft.location_id = form.location_id
  if (form.tool_id !== UNCHOSEN) draft.tool_id = form.tool_id
  draft.references = form.references.map((row) => ({ name: row.name ?? '', url: row.url ?? '' }))
  draft.notes = form.notes
  return {
    drill_id: drillId,
    exercise_id: drillId === null ? integerOrNull(form.exercise_id) : null,
    draft,
  }
}

// ------------------------------------------------------------------- sound

/**
 * A short tone through Web Audio - no asset to ship. Returns whether it was
 * played. The tab has already been clicked by then (the timer was started
 * from it), so the browser's autoplay rule allows a new context.
 */
export function playTone(AudioContextClass = globalThis.AudioContext ?? globalThis.webkitAudioContext) {
  if (!AudioContextClass) return false
  try {
    const context = new AudioContextClass()
    const start = context.currentTime
    const oscillator = context.createOscillator()
    const gain = context.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.setValueAtTime(880, start)
    gain.gain.setValueAtTime(0.0001, start)
    gain.gain.exponentialRampToValueAtTime(0.3, start + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.9)
    oscillator.connect(gain)
    gain.connect(context.destination)
    oscillator.onended = () => context.close?.()
    oscillator.start(start)
    oscillator.stop(start + 1)
    return true
  } catch {
    return false
  }
}
