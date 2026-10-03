// Frontend: the exercise library's grouping, and the words for a drill's
// numbers.
//
// Every read of an exercise summary's `stage` and of a drill's amount fields
// is here, so a field the API renames is a one-line fix.

export const NO_STAGE_TITLE = '不分階段'

/** A stage reference `{ id, number, display_name }` as words. */
export function stageTitle(stage) {
  return `階段 ${stage.number} · ${stage.display_name}`
}

/**
 * Exercise summaries grouped by stage, in roadmap order - a stage's `number`
 * counts from 0 across the whole roadmap, so it is the order - and then the
 * exercises with no stage, under 不分階段. Inside a group the server's order is
 * kept. Returns [{ key, stage, title, exercises }].
 */
export function groupByStage(exercises) {
  const groups = new Map()
  for (const exercise of exercises ?? []) {
    const stage = exercise.stage ?? null
    const key = stage ? `stage-${stage.id}` : 'none'
    if (!groups.has(key)) {
      groups.set(key, { key, stage, title: stage ? stageTitle(stage) : NO_STAGE_TITLE, exercises: [] })
    }
    groups.get(key).exercises.push(exercise)
  }
  return [...groups.values()].sort((a, b) => {
    if (!a.stage) return b.stage ? 1 : 0
    if (!b.stage) return -1
    return a.stage.number - b.stage.number
  })
}

/** A drill's round as words - "20 張", "頁" - or null when it has neither. */
export function drillAmount(drill) {
  const parts = [drill.target, drill.unit].filter((part) => part != null && part !== '')
  return parts.length ? parts.join(' ') : null
}

/** Minutes as words, "90 分鐘", or null for none. */
export function minutesLabel(minutes) {
  return minutes == null ? null : `${minutes} 分鐘`
}
