import { describe, expect, it } from 'vitest'

import { goalStatusLabel, inProgressStages, localToday, stageStatusLabel } from './roadmap'

describe('inProgressStages', () => {
  it('is every stage in progress, wherever it is, in roadmap order', () => {
    const goals = [
      { id: 1, stages: [{ id: 10, status: 'passed' }, { id: 11, status: 'not_started' }, { id: 12, status: 'in_progress' }] },
      { id: 2, stages: [] },
      { id: 3, stages: [{ id: 30, status: 'in_progress' }, { id: 31, status: 'not_started' }] },
    ]
    expect(inProgressStages(goals).map(({ goal, stage }) => [goal.id, stage.id])).toEqual([
      [1, 12],
      [3, 30],
    ])
  })

  it('is empty when nothing is in progress, or there are no goals', () => {
    expect(inProgressStages([{ id: 1, stages: [{ id: 10, status: 'not_started' }] }])).toEqual([])
    expect(inProgressStages([])).toEqual([])
    expect(inProgressStages(undefined)).toEqual([])
  })
})

describe('labels', () => {
  it('words each status, and falls back to the value', () => {
    expect(goalStatusLabel('achieved')).toBe('已達成')
    expect(stageStatusLabel('in_progress')).toBe('進行中')
    expect(stageStatusLabel('mystery')).toBe('mystery')
  })
})

describe('localToday', () => {
  it('is the local calendar date, zero-padded', () => {
    expect(localToday(new Date(2026, 0, 5, 23, 59))).toBe('2026-01-05')
  })
})
