import { describe, expect, it } from 'vitest'

import {
  emptyRecordForm,
  fromRecord,
  groupByDate,
  recordDrillName,
  recordToPayload,
  summaryMinutes,
  UNCHOSEN,
  weekRange,
} from './records'

describe('weekRange', () => {
  it('runs Monday to Sunday', () => {
    expect(weekRange('2026-10-03')).toEqual({ from: '2026-09-28', to: '2026-10-04' })
  })

  it('puts a Sunday at the end of its week, not the start of the next', () => {
    expect(weekRange('2026-10-04')).toEqual({ from: '2026-09-28', to: '2026-10-04' })
    expect(weekRange('2026-09-28')).toEqual({ from: '2026-09-28', to: '2026-10-04' })
  })
})

describe('groupByDate', () => {
  it('groups newest first and totals each day, a record with no duration as zero', () => {
    const days = groupByDate([
      { id: 1, date: '2026-10-01', duration_minutes: 15 },
      { id: 2, date: '2026-10-02', duration_minutes: 30 },
      { id: 3, date: '2026-10-02', duration_minutes: null },
      { id: 4, date: '2026-10-02', duration_minutes: 15 },
    ])
    expect(days.map(({ date, minutes, records }) => [date, minutes, records.map((r) => r.id)])).toEqual([
      ['2026-10-02', 45, [2, 3, 4]],
      ['2026-10-01', 15, [1]],
    ])
  })

  it('sums the summary rows', () => {
    expect(summaryMinutes([{ minutes: 45 }, { minutes: 0 }, { minutes: 15 }])).toBe(60)
    expect(summaryMinutes(undefined)).toBe(0)
  })
})

describe('recordDrillName', () => {
  it('is the drill only when its name is its own', () => {
    const exercise = { id: 1, display_name: '線條' }
    expect(recordDrillName({ activity: { exercise, drill: { id: 5, display_name: '基本線條' } } })).toBe('基本線條')
    expect(recordDrillName({ activity: { exercise, drill: { id: 6, display_name: '線條' } } })).toBeNull()
    expect(recordDrillName({ activity: null })).toBeNull()
  })
})

describe('recordToPayload', () => {
  const base = { ...emptyRecordForm({ today: '2026-10-03' }), location_id: null, tool_id: null }

  it('sends a drill without its exercise', () => {
    const body = recordToPayload({ ...base, exercise_id: '1', drill_id: '5' })
    expect(body.drill_id).toBe(5)
    expect(body.exercise_id).toBeNull()
  })

  it('sends an exercise alone when no drill is chosen', () => {
    const body = recordToPayload({ ...base, exercise_id: '1', drill_id: '' })
    expect(body.drill_id).toBeNull()
    expect(body.exercise_id).toBe(1)
  })

  it('sends a test target only for a test, and exactly one of stage and level', () => {
    expect(recordToPayload({ ...base, kind: 'test', target: 'goal:2' })).toMatchObject({ stage_id: null, goal_id: 2 })
    expect(recordToPayload({ ...base, kind: 'test', target: 'stage:11' })).toMatchObject({ stage_id: 11, goal_id: null })
    // A target left behind by switching the kind away from test is not sent.
    expect(recordToPayload({ ...base, kind: 'piece', target: 'stage:11' })).toMatchObject({
      stage_id: null,
      goal_id: null,
    })
  })

  it('resolves an unchosen location and tool to their defaults, and a cleared one to null', () => {
    const fresh = emptyRecordForm({ today: '2026-10-03' })
    expect(fresh.location_id).toBe(UNCHOSEN)
    expect(recordToPayload(fresh, { location_id: 31, tool_id: 41 })).toMatchObject({ location_id: 31, tool_id: 41 })
    expect(recordToPayload({ ...fresh, tool_id: null }, { location_id: 31, tool_id: 41 }).tool_id).toBeNull()
  })

  it('round-trips a test record through the form', () => {
    const record = {
      date: '2026-10-02',
      location: { id: 31 },
      duration_minutes: 60,
      activity: { exercise: { id: 1, display_name: '線條' }, drill: null },
      kind: 'test',
      stage: { id: 11, number: 1, display_name: '線條與形狀' },
      goal: null,
      method: null,
      tool: { id: 41 },
      references: [{ id: 1, name: 'ref', url: 'https://r.example' }],
      notes: '穩',
    }
    expect(recordToPayload(fromRecord(record))).toEqual({
      date: '2026-10-02',
      location_id: 31,
      duration_minutes: 60,
      drill_id: null,
      exercise_id: 1,
      kind: 'test',
      stage_id: 11,
      goal_id: null,
      method_id: null,
      tool_id: 41,
      references: [{ name: 'ref', url: 'https://r.example' }],
      notes: '穩',
    })
  })
})
