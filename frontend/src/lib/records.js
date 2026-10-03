// Frontend: records - their kinds, how one is read, grouped and totalled, and
// the record form's conversions.
//
// Every read of a record's fields goes through here, so a field the API
// renames is a one-line fix. The kinds are the backend's `RecordKind` enum
// (app/constants.py).
import { localToday, parseTarget, targetValue } from './roadmap'
import { blankToNull, integerOrNull, resourcesFromApi, resourcesToPayload } from './rowList'

export const RECORD_KINDS = [
  { value: 'practice', label: '練習' },
  { value: 'piece', label: '作品' },
  { value: 'test', label: '測驗' },
]

export const DEFAULT_RECORD_KIND = 'practice'
export const TEST_KIND = 'test'

/** The tool a new record starts with, matched by the option's value. */
export const DEFAULT_TOOL = 'Clip Studio Paint'

/** The word for a kind, or the value itself. */
export function recordKindLabel(value) {
  return RECORD_KINDS.find((entry) => entry.value === value)?.label ?? value
}

// ---------------------------------------------------------------- reading

/** The exercise a record names, directly or through its drill - `{ id, display_name }` - or null. */
export function recordExercise(record) {
  return record.activity?.exercise ?? null
}

/** The drill a record names, `{ id, display_name }`, or null. */
export function recordDrill(record) {
  return record.activity?.drill ?? null
}

/**
 * The drill's name when it has one of its own. A drill's display name falls
 * back to its exercise's, and the exercise is already shown.
 */
export function recordDrillName(record) {
  const drill = recordDrill(record)
  if (!drill) return null
  return drill.display_name === recordExercise(record)?.display_name ? null : drill.display_name
}

/** What a test record tests: "L0 基礎" for a level, "階段 1 · 線條與形狀" for a stage, or null. */
export function recordTestTarget(record) {
  if (record.goal) return `${record.goal.code} ${record.goal.display_name}`
  if (record.stage) return `階段 ${record.stage.number} · ${record.stage.display_name}`
  return null
}

/** A record's minutes; a record with no duration counts as zero. */
export function recordMinutes(record) {
  return record.duration_minutes ?? 0
}

/** Whether the record has a duration at all. */
export function recordHasDuration(record) {
  return record.duration_minutes != null
}

/** The options a record carries, in reading order - location, method, tool - as OptionRefs. */
export function recordOptions(record) {
  return [record.location, record.method, record.tool].filter(Boolean)
}

export function recordReferences(record) {
  return record.references ?? []
}

export function recordNotes(record) {
  return record.notes ?? null
}

/**
 * Records grouped by date, newest first, each with its total minutes:
 * [{ date, records, minutes }]. Inside a day the given order is kept.
 */
export function groupByDate(records) {
  const days = new Map()
  for (const record of records ?? []) {
    if (!days.has(record.date)) days.set(record.date, { date: record.date, records: [], minutes: 0 })
    const day = days.get(record.date)
    day.records.push(record)
    day.minutes += recordMinutes(record)
  }
  return [...days.values()].sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))
}

/** Total minutes over GET /api/records/summary's rows, `[{ date, minutes, records }]`. */
export function summaryMinutes(rows) {
  return (rows ?? []).reduce((total, row) => total + (row.minutes ?? 0), 0)
}

// ------------------------------------------------------------------ dates

function parseDate(text) {
  const [year, month, day] = text.split('-').map(Number)
  return new Date(year, month - 1, day)
}

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']

/** The weekday of a YYYY-MM-DD, as 一 … 日. */
export function weekdayLabel(text) {
  return WEEKDAYS[parseDate(text).getDay()]
}

/** The Monday-to-Sunday week holding `today` (YYYY-MM-DD), as { from, to }. */
export function weekRange(today = localToday()) {
  const date = parseDate(today)
  const back = (date.getDay() + 6) % 7
  const monday = new Date(date.getFullYear(), date.getMonth(), date.getDate() - back)
  const sunday = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 6)
  return { from: localToday(monday), to: localToday(sunday) }
}

// ------------------------------------------------------------------- form

/**
 * A field not chosen yet takes its default once the page has loaded it: the
 * newest record's location, the Clip Studio Paint tool. A click replaces it
 * with an id or with null, so clearing a default sticks.
 */
export const UNCHOSEN = 'unchosen'

/** A new record's form. `drill` and `exercise` are the ?drill= / ?exercise= ids, or null. */
export function emptyRecordForm({ today = localToday(), drill = null, exercise = null } = {}) {
  return {
    date: today,
    location_id: UNCHOSEN,
    duration_minutes: '',
    exercise_id: exercise ?? '',
    drill_id: drill ?? '',
    kind: DEFAULT_RECORD_KIND,
    target: '',
    method_id: null,
    tool_id: UNCHOSEN,
    references: [],
    notes: '',
  }
}

/** A record as the API serves it, as the form's state. */
export function fromRecord(record) {
  const exercise = recordExercise(record)
  const drill = recordDrill(record)
  let target = ''
  if (record.goal) target = targetValue('goal', record.goal.id)
  else if (record.stage) target = targetValue('stage', record.stage.id)
  return {
    date: record.date ?? '',
    location_id: record.location?.id ?? null,
    duration_minutes: record.duration_minutes == null ? '' : String(record.duration_minutes),
    exercise_id: exercise ? String(exercise.id) : '',
    drill_id: drill ? String(drill.id) : '',
    kind: record.kind ?? DEFAULT_RECORD_KIND,
    target,
    method_id: record.method?.id ?? null,
    tool_id: record.tool?.id ?? null,
    references: resourcesFromApi(record.references),
    notes: record.notes ?? '',
  }
}

/** The location of the newest record, given GET /api/records (newest first). */
export function latestLocationId(records) {
  return records?.[0]?.location?.id ?? null
}

/** The id of the Clip Studio Paint tool option, or null. */
export function defaultToolId(tools) {
  return (tools ?? []).find((option) => option.value === DEFAULT_TOOL)?.id ?? null
}

/** A field's value with UNCHOSEN resolved to its default. */
export function chosen(value, fallback) {
  return value === UNCHOSEN ? (fallback ?? null) : value
}

/**
 * The form as the API's RecordWrite. A record names a drill or an exercise,
 * never both: with a drill, the server derives the exercise and it is sent as
 * null. A test names exactly one stage or one level; any other kind neither.
 * `defaults` is { location_id, tool_id } for fields still UNCHOSEN.
 */
export function recordToPayload(form, defaults = {}) {
  const drillId = integerOrNull(form.drill_id)
  const target = form.kind === TEST_KIND ? parseTarget(form.target) : { stage_id: null, goal_id: null }
  return {
    date: form.date,
    location_id: chosen(form.location_id, defaults.location_id),
    duration_minutes: integerOrNull(form.duration_minutes),
    drill_id: drillId,
    exercise_id: drillId === null ? integerOrNull(form.exercise_id) : null,
    kind: form.kind,
    stage_id: target.stage_id,
    goal_id: target.goal_id,
    method_id: form.method_id,
    tool_id: chosen(form.tool_id, defaults.tool_id),
    references: resourcesToPayload(form.references),
    notes: blankToNull(form.notes),
  }
}
