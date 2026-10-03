import { describe, expect, it } from 'vitest'

import { currentStageId, goalStatusLabel, localToday, stageStatusLabel } from './roadmap'

describe('currentStageId', () => {
  it('is the first stage not passed, across goals in order', () => {
    const goals = [
      { id: 1, stages: [{ id: 10, status: 'passed' }, { id: 11, status: 'passed' }] },
      { id: 2, stages: [] },
      { id: 3, stages: [{ id: 30, status: 'not_started' }, { id: 31, status: 'in_progress' }] },
    ]
    expect(currentStageId(goals)).toBe(30)
  })

  it('is null when every stage is passed, or there are none', () => {
    expect(currentStageId([{ id: 1, stages: [{ id: 10, status: 'passed' }] }])).toBeNull()
    expect(currentStageId([])).toBeNull()
    expect(currentStageId(undefined)).toBeNull()
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
