// Frontend: the roadmap's statuses and their words, and what the roadmap
// derives from its goals.
//
// The values are the backend's `GoalStatus` and `StageStatus` enums
// (app/constants.py). Status is set by hand: nothing here derives a goal's
// status from its stages.
//
// Each status carries the Chip tone it is drawn in (components/ui/primitives):
// `brand` for what is being worked on now, `ok` for done, `neutral` for not yet.

export const GOAL_STATUSES = [
  { value: 'planned', label: '計畫中', tone: 'neutral' },
  { value: 'active', label: '進行中', tone: 'brand' },
  { value: 'achieved', label: '已達成', tone: 'ok' },
]

export const STAGE_STATUSES = [
  { value: 'not_started', label: '未開始', tone: 'neutral' },
  { value: 'in_progress', label: '進行中', tone: 'brand' },
  { value: 'passed', label: '已通過', tone: 'ok' },
]

export const DEFAULT_GOAL_STATUS = 'planned'
export const DEFAULT_STAGE_STATUS = 'not_started'

// The status that carries a date: `achieved_on` / `passed_on` is set only
// with it, and the server clears the date when the status moves away.
export const GOAL_DONE = 'achieved'
export const STAGE_DONE = 'passed'

// What is being worked on now. Any number of stages and levels may be at
// once, anywhere on the roadmap: the owner does not work top to bottom.
export const GOAL_ACTIVE = 'active'
export const STAGE_ACTIVE = 'in_progress'

function find(list, value) {
  return list.find((entry) => entry.value === value)
}

/** The word for a goal status, or the value itself. */
export function goalStatusLabel(value) {
  return find(GOAL_STATUSES, value)?.label ?? value
}

/** The word for a stage status, or the value itself. */
export function stageStatusLabel(value) {
  return find(STAGE_STATUSES, value)?.label ?? value
}

export function goalStatusTone(value) {
  return find(GOAL_STATUSES, value)?.tone ?? 'neutral'
}

export function stageStatusTone(value) {
  return find(STAGE_STATUSES, value)?.tone ?? 'neutral'
}

/**
 * Every stage in progress as { goal, stage }, in roadmap order. `goals` is
 * GET /api/goals, already in that order with each goal's stages in theirs.
 */
export function inProgressStages(goals) {
  return (goals ?? []).flatMap((goal) =>
    (goal.stages ?? []).filter((stage) => stage.status === STAGE_ACTIVE).map((stage) => ({ goal, stage })),
  )
}

/** Today in the browser's own time zone, as the API's YYYY-MM-DD. */
export function localToday(now = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/**
 * One stage or one level, chosen in a single select (components/forms/
 * RoadmapSelect): encoded `stage:<id>` / `goal:<id>`, so a test record's
 * "exactly one of the two" is the shape of the control.
 */
export function targetValue(kind, id) {
  return `${kind}:${id}`
}

/** A `stage:<id>` / `goal:<id>` choice as { stage_id, goal_id }; '' is neither. */
export function parseTarget(value) {
  const match = /^(stage|goal):(\d+)$/.exec(value ?? '')
  return {
    stage_id: match?.[1] === 'stage' ? Number(match[2]) : null,
    goal_id: match?.[1] === 'goal' ? Number(match[2]) : null,
  }
}
