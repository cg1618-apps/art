import { describe, expect, it } from 'vitest'

import { drillAmount, groupByStage, NO_STAGE_TITLE } from './exercises'

const stage = (id, number, display_name) => ({ id, number, display_name })

describe('groupByStage', () => {
  it('orders the groups by stage number and puts the exercises with no stage last', () => {
    // The server's order (by name) is deliberately not the roadmap's.
    const exercises = [
      { id: 1, display_name: '動態速寫', stage: null },
      { id: 2, display_name: '透視方塊', stage: stage(12, 2, '空間中的形體') },
      { id: 3, display_name: '線條', stage: stage(11, 1, '線條與形狀') },
      { id: 4, display_name: '基本形體', stage: stage(12, 2, '空間中的形體') },
      { id: 5, display_name: '角色作品', stage: null },
    ]
    const groups = groupByStage(exercises)
    expect(groups.map((group) => group.title)).toEqual(['階段 1 · 線條與形狀', '階段 2 · 空間中的形體', NO_STAGE_TITLE])
    expect(groups.map((group) => group.exercises.map((exercise) => exercise.id))).toEqual([[3], [2, 4], [1, 5]])
  })

  it('draws no 不分階段 group when every exercise has a stage', () => {
    const groups = groupByStage([{ id: 1, stage: stage(11, 0, '設定') }])
    expect(groups.map((group) => group.title)).toEqual(['階段 0 · 設定'])
  })
})

describe('drillAmount', () => {
  it('reads target and unit as words, or null for neither', () => {
    expect(drillAmount({ target: 20, unit: '張' })).toBe('20 張')
    expect(drillAmount({ target: null, unit: '頁' })).toBe('頁')
    expect(drillAmount({ target: null, unit: null })).toBeNull()
  })
})
