// The drill pages through the real routes, with fetch mocked: the library
// groups by its exercises' stages in roadmap order with 不分階段 last and keeps
// its topic and source filters in the URL; the drill page shows its exercise
// and stage, its facts and buttons, and reads its records by drill_id; and the
// navigation marks 練法, not 練習, on a drill's page.
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { currentLocation, json, renderAt, stubFetch } from './pageHarness'

const stageRef = (id, number, display_name) => ({ id, number, display_name })
const LINES = stageRef(11, 1, '線條與形狀')
const FORMS = stageRef(12, 2, '空間中的形體')
const CAS = { id: 20, value: 'Character Art School', description: null }

const summary = (fields) => ({
  name: fields.display_name,
  stage: null,
  topics: [],
  source: null,
  unit: null,
  target: null,
  suggested_minutes: null,
  frequency: null,
  record_count: 0,
  total_minutes: 0,
  ...fields,
})

// Not the roadmap's order: a library that drew groups in arrival order would
// put 不分階段 first and stage 2 before 1.
const DRILLS = [
  summary({ id: 9, display_name: '三十秒', exercise: { id: 8, display_name: '動態速寫' } }),
  summary({ id: 7, display_name: '透視盒子', exercise: { id: 5, display_name: '透視方塊' }, stage: FORMS }),
  summary({
    id: 5,
    display_name: '基本線條',
    exercise: { id: 1, display_name: '線條' },
    stage: LINES,
    source: CAS,
    unit: '頁',
    target: 1,
    suggested_minutes: 10,
    frequency: '每天',
    record_count: 2,
    total_minutes: 25,
  }),
]

const TOPICS = [{ id: 10, category: 'topic', value: '透視', description: null, sort_order: 0, in_use: 0 }]
const SOURCES = [{ id: 20, category: 'source', ...CAS, sort_order: 0, in_use: 0 }]

const DRILL = {
  id: 5,
  exercise: { id: 1, display_name: '線條' },
  name: '基本線條',
  display_name: '基本線條',
  source: CAS,
  source_links: [{ id: 1, name: '作業表', url: 'https://example.com/sheet' }],
  resources: [],
  instructions: '直線、**弧線**。',
  unit: '頁',
  target: 1,
  suggested_minutes: 10,
  frequency: '每天',
  remark: '先暖身',
  position: 0,
}

const EXERCISE = {
  id: 1,
  display_name: '線條',
  name_cn: '線條',
  name_en: null,
  name_alt: null,
  stage: LINES,
  topics: [],
  description: null,
  drill_count: 1,
  record_count: 3,
  total_minutes: 50,
  aliases: [],
  remark: null,
  resources: [],
  drills: [DRILL],
}

const record = (id, duration_minutes, notes) => ({
  id,
  date: '2026-10-02',
  location: null,
  duration_minutes,
  activity: { exercise: { id: 1, display_name: '線條' }, drill: { id: 5, display_name: '基本線條' } },
  kind: 'practice',
  stage: null,
  goal: null,
  method: null,
  tool: null,
  references: [],
  notes,
})

const RECORDS = [record(71, 15, '手腕太用力'), record(70, null, null)]

let calls

function respond(call) {
  const [path, query = ''] = call.url.split('?')
  if (path === '/api/options') {
    if (query.includes('category=topic')) return json(TOPICS)
    if (query.includes('category=source')) return json(SOURCES)
    return json([])
  }
  if (path === '/api/drills') return json(DRILLS)
  if (path === '/api/drills/5') return json(DRILL)
  if (path === '/api/exercises/1') return json(EXERCISE)
  if (path === '/api/records') return json(RECORDS)
  if (path === '/api/timer') return json(null)
  return json([])
}

beforeEach(() => {
  calls = stubFetch(respond)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('the drill library', () => {
  it('groups by the exercise’s stage in roadmap order, then 不分階段', async () => {
    renderAt('/drills')
    const first = await screen.findByRole('list', { name: '階段 1 · 線條與形狀' })
    const headings = screen.getAllByRole('heading', { level: 2 }).map((heading) => heading.textContent)
    expect(headings).toEqual(['階段 1 · 線條與形狀', '階段 2 · 空間中的形體', '不分階段'])

    const card = within(first).getByRole('link')
    expect(card.getAttribute('href')).toBe('/drills/5')
    expect(within(card).getByText('線條')).toBeTruthy()
    expect(within(card).getByText('Character Art School')).toBeTruthy()
    expect(within(card).getByText('1 頁 · 10 分鐘 · 每天')).toBeTruthy()
    expect(within(card).getByText('2 筆紀錄 · 25 分鐘')).toBeTruthy()

    const none = screen.getByRole('list', { name: '不分階段' })
    expect(within(none).getByText('三十秒')).toBeTruthy()
    expect(within(none).getByText('0 筆紀錄 · 0 分鐘')).toBeTruthy()
  })

  it('keeps the topic and source filters in the URL and sends them as topic_id and source_id', async () => {
    renderAt('/drills')
    fireEvent.click(await screen.findAllByRole('button', { name: '透視' }).then((buttons) => buttons[0]))
    await waitFor(() => expect(currentLocation()).toBe('/drills?topic=10'))
    fireEvent.click(await screen.findAllByRole('button', { name: 'Character Art School' }).then((b) => b[0]))
    await waitFor(() => expect(currentLocation()).toBe('/drills?topic=10&source=20'))
    await waitFor(() =>
      expect(calls.some((call) => call.url === '/api/drills?topic_id=10&source_id=20')).toBe(true),
    )
  })

  it('says so when nothing matches, and offers clearing', async () => {
    stubFetch((call) => (call.url.startsWith('/api/drills?') ? json([]) : respond(call)))
    renderAt('/drills?source=20')
    expect(await screen.findByText('沒有符合條件的練法。')).toBeTruthy()
    expect(screen.getByRole('button', { name: '清除搜尋與篩選' })).toBeTruthy()
  })
})

describe('a drill', () => {
  it('shows its exercise, stage, source, facts and buttons, and its records', async () => {
    renderAt('/drills/5')
    expect(await screen.findByRole('heading', { level: 1, name: '基本線條' })).toBeTruthy()
    expect(screen.getByRole('link', { name: '線條' }).getAttribute('href')).toBe('/exercises/1')
    expect((await screen.findByRole('link', { name: '階段 1 · 線條與形狀' })).getAttribute('href')).toBe(
      '/roadmap/stages/11',
    )
    expect(screen.getByText('Character Art School')).toBeTruthy()
    expect(screen.getByText('1 頁 · 10 分鐘 · 每天')).toBeTruthy()
    expect(screen.getByRole('link', { name: '記錄' }).getAttribute('href')).toBe('/records/new?drill=5')
    expect(screen.getByRole('button', { name: '為「基本線條」開始計時' })).toBeTruthy()
    expect(screen.getByRole('link', { name: '編輯' }).getAttribute('href')).toBe('/drills/5/edit')
    expect(screen.getByText('弧線').tagName).toBe('STRONG')
    expect(screen.getByRole('link', { name: /作業表/ }).getAttribute('href')).toBe('https://example.com/sheet')
    expect(screen.getByText('先暖身')).toBeTruthy()

    const records = await screen.findByRole('list', { name: '「基本線條」的紀錄' })
    expect(within(records).getByText('手腕太用力')).toBeTruthy()
    // A record with no duration counts as a record and zero minutes.
    expect(screen.getByText('共 2 筆 · 15 分鐘')).toBeTruthy()
    expect(calls.some((call) => call.url === '/api/records?drill_id=5')).toBe(true)
  })

  it('marks 練法 in the navigation, not 練習', async () => {
    renderAt('/drills/5')
    await screen.findByRole('heading', { level: 1, name: '基本線條' })
    const nav = screen.getAllByRole('navigation', { name: '主要' })[0]
    expect(within(nav).getByRole('link', { name: '練法' }).getAttribute('aria-current')).toBe('page')
    expect(within(nav).getByRole('link', { name: '練習' }).getAttribute('aria-current')).toBeNull()
  })

  it('says it cannot be found for a 404', async () => {
    stubFetch((call) => (call.url === '/api/drills/99' ? json({ detail: 'No such drill.' }, 404) : respond(call)))
    renderAt('/drills/99')
    expect(await screen.findByText('找不到這個練法。')).toBeTruthy()
  })
})

describe('the drill form', () => {
  it('goes to the drill’s page after an edit', async () => {
    calls = stubFetch((call) => (call.method === 'PATCH' ? json(DRILL) : respond(call)))
    renderAt('/drills/5/edit')
    expect(await screen.findByDisplayValue('基本線條')).toBeTruthy()
    await waitFor(() => expect(screen.getByRole('button', { name: '儲存' })).toBeTruthy())
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(currentLocation()).toBe('/drills/5'))
    expect(calls.filter((call) => call.method === 'PATCH').map((call) => call.url)).toEqual(['/api/drills/5'])
  })

  it('goes back to the drill’s page on Cancel', async () => {
    renderAt('/drills/5/edit')
    expect(await screen.findByDisplayValue('基本線條')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '取消' }))
    await waitFor(() => expect(currentLocation()).toBe('/drills/5'))
  })
})
