// The exercise pages through the real routes, with fetch mocked: the library
// groups by stage in roadmap order with 不分階段 last and keeps its topic
// filter in the URL; the exercise page shows its drills, each named by a link
// to its own page, with 記錄 links, and reads its records by exercise_id; the
// exercise and drill forms send their write shapes.
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { currentLocation, json, renderAt, stubFetch } from './pageHarness'

const stageRef = (id, number, display_name) => ({ id, number, display_name })
const LINES = stageRef(11, 1, '線條與形狀')
const FORMS = stageRef(12, 2, '空間中的形體')

const summary = (fields) => ({
  name_cn: fields.display_name,
  name_en: null,
  name_alt: null,
  stage: null,
  topics: [],
  description: null,
  drill_count: 0,
  record_count: 0,
  total_minutes: 0,
  ...fields,
})

// The server orders by name, which is not the roadmap's order: a library that
// drew groups in arrival order would put 不分階段 first and stage 2 before 1.
const EXERCISES = [
  summary({ id: 8, display_name: '動態速寫', description: '限時抓動態。' }),
  summary({ id: 5, display_name: '透視方塊', stage: FORMS }),
  summary({ id: 1, display_name: '線條', stage: LINES, drill_count: 2, record_count: 3, total_minutes: 50 }),
  summary({ id: 4, display_name: '基本形體', stage: FORMS }),
]

const TOPICS = [{ id: 10, category: 'topic', value: '透視', description: '空間的遠近', sort_order: 0, in_use: 0 }]
const SOURCES = [{ id: 20, category: 'source', value: '自訂', description: null, sort_order: 0, in_use: 0 }]

const DRILL = {
  id: 5,
  exercise: { id: 1, display_name: '線條' },
  name: '基本線條',
  display_name: '基本線條',
  source: { id: 20, value: '自訂', description: null },
  source_links: [{ id: 1, name: 'Line of Action', url: 'https://line-of-action.com/' }],
  resources: [],
  instructions: '直線、**弧線**。',
  unit: '頁',
  target: 1,
  suggested_minutes: 10,
  frequency: '每天（暖身）',
  remark: null,
  position: 0,
}

const EXERCISE = {
  ...EXERCISES[2],
  name_en: 'Lines',
  description: '穩定的直線與曲線。',
  topics: [{ id: 10, value: '透視', description: '空間的遠近' }],
  aliases: [],
  remark: null,
  resources: [],
  drills: [DRILL],
}

const RECORDS = [
  {
    id: 70,
    date: '2026-10-02',
    location: null,
    duration_minutes: 30,
    activity: { exercise: { id: 1, display_name: '線條' }, drill: { id: 5, display_name: '基本線條' } },
    kind: 'practice',
    stage: null,
    goal: null,
    method: null,
    tool: null,
    references: [],
    notes: '手腕太用力',
  },
]

const GOALS = [
  { id: 1, code: 'L0', display_name: '基礎', stages: [{ ...LINES }, { ...FORMS }] },
]

let calls
let handler

function defaultResponse(call) {
  const [path, query = ''] = call.url.split('?')
  if (path === '/api/options') {
    if (query.includes('category=topic')) return json(TOPICS)
    if (query.includes('category=source')) return json(SOURCES)
    return json([])
  }
  if (path === '/api/exercises') return json(EXERCISES)
  if (path === '/api/exercises/1') return json(EXERCISE)
  if (path === '/api/drills/5') return json(DRILL)
  if (path === '/api/records') return json(RECORDS)
  if (path === '/api/goals') return json(GOALS)
  return json([])
}

const writes = (method) => calls.filter((call) => call.method === method)

beforeEach(() => {
  handler = () => null
  calls = stubFetch((call) => handler(call) ?? defaultResponse(call))
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('the exercise library', () => {
  it('groups by stage in roadmap order, then 不分階段', async () => {
    renderAt('/exercises')
    const first = await screen.findByRole('list', { name: '階段 1 · 線條與形狀' })
    const headings = screen.getAllByRole('heading', { level: 2 }).map((heading) => heading.textContent)
    expect(headings).toEqual(['階段 1 · 線條與形狀', '階段 2 · 空間中的形體', '不分階段'])

    expect(within(first).getByRole('link').getAttribute('href')).toBe('/exercises/1')
    expect(within(first).getByText('2 個練法 · 3 筆紀錄 · 50 分鐘')).toBeTruthy()
    const second = screen.getByRole('list', { name: '階段 2 · 空間中的形體' })
    expect(within(second).getAllByRole('listitem').map((item) => item.textContent)).toEqual([
      expect.stringContaining('透視方塊'),
      expect.stringContaining('基本形體'),
    ])
    const none = screen.getByRole('list', { name: '不分階段' })
    expect(within(none).getByText('限時抓動態。')).toBeTruthy()
  })

  it('keeps the topic filter in the URL and sends it as topic_id', async () => {
    renderAt('/exercises')
    fireEvent.click(await screen.findAllByRole('button', { name: '透視' }).then((buttons) => buttons[0]))
    await waitFor(() => expect(currentLocation()).toBe('/exercises?topic=10'))
    await waitFor(() => expect(calls.some((call) => call.url === '/api/exercises?topic_id=10')).toBe(true))
  })
})

describe('an exercise', () => {
  it('shows its stage, drills with a 記錄 link each, and its records', async () => {
    renderAt('/exercises/1')
    expect(await screen.findByRole('heading', { level: 1, name: '線條' })).toBeTruthy()
    expect(screen.getByRole('link', { name: '階段 1 · 線條與形狀' }).getAttribute('href')).toBe('/roadmap/stages/11')
    expect(screen.getByText('Lines')).toBeTruthy()

    const drills = screen.getByRole('list', { name: '練法' })
    expect(within(drills).getByRole('heading', { name: '基本線條' })).toBeTruthy()
    expect(within(drills).getByRole('link', { name: '基本線條' }).getAttribute('href')).toBe('/drills/5')
    expect(within(drills).getByText('1 頁 · 10 分鐘 · 每天（暖身）')).toBeTruthy()
    expect(within(drills).getByText('弧線').tagName).toBe('STRONG')
    expect(within(drills).getByRole('link', { name: /Line of Action/ }).getAttribute('href')).toBe(
      'https://line-of-action.com/',
    )
    expect(within(drills).getByRole('link', { name: '記錄「基本線條」' }).getAttribute('href')).toBe(
      '/records/new?drill=5',
    )

    const records = await screen.findByRole('list', { name: '「線條」的紀錄' })
    expect(within(records).getByText('手腕太用力')).toBeTruthy()
    expect(screen.getByText('共 3 筆 · 50 分鐘')).toBeTruthy()
    expect(calls.some((call) => call.url === '/api/records?exercise_id=1')).toBe(true)
  })

  it('shows the server refusing to delete an exercise that has drills', async () => {
    handler = (call) =>
      call.method === 'DELETE' ? json({ detail: '這個練習項目還有 1 個練法、3 筆紀錄。', drills: 1, records: 3 }, 409) : null
    renderAt('/exercises/1')
    fireEvent.click(await screen.findByRole('button', { name: '刪除' }))
    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: '刪除' }))
    expect(await within(dialog).findByText('這個練習項目還有 1 個練法、3 筆紀錄。')).toBeTruthy()
    expect(currentLocation()).toBe('/exercises/1')
  })
})

describe('the exercise form', () => {
  it('sends the stage, topics and resources', async () => {
    handler = (call) => (call.method === 'POST' ? json({ ...EXERCISE, id: 9 }, 201) : null)
    renderAt('/exercises/new')
    fireEvent.change(screen.getByRole('textbox', { name: '中文名' }), { target: { value: ' 陰影 ' } })
    fireEvent.change(screen.getByRole('textbox', { name: /別名/ }), { target: { value: 'shade、影' } })
    const stage = screen.getByRole('combobox', { name: /階段/ })
    await waitFor(() => expect(within(stage).getAllByRole('option')).toHaveLength(3))
    fireEvent.change(stage, { target: { value: 'stage:12' } })
    fireEvent.click(await screen.findByRole('button', { name: '透視' }))
    fireEvent.click(screen.getByRole('button', { name: /新增資源/ }))
    fireEvent.change(screen.getByRole('textbox', { name: '資源 1 連結' }), { target: { value: 'https://s.example' } })

    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(currentLocation()).toBe('/exercises/9'))
    expect(writes('POST')[0]).toMatchObject({ url: '/api/exercises' })
    expect(writes('POST')[0].body).toEqual({
      name_cn: '陰影',
      name_en: null,
      name_alt: null,
      aliases: ['shade', '影'],
      stage_id: 12,
      topic_ids: [10],
      description: null,
      remark: null,
      resources: [{ name: null, url: 'https://s.example' }],
    })
  })

  it('sends no stage for 不分階段', async () => {
    handler = (call) => (call.method === 'PATCH' ? json(EXERCISE) : null)
    renderAt('/exercises/1/edit')
    expect(await screen.findByDisplayValue('Lines')).toBeTruthy()
    const stage = screen.getByRole('combobox', { name: /階段/ })
    await waitFor(() => expect(stage.value).toBe('stage:11'))
    fireEvent.change(stage, { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(writes('PATCH')).toHaveLength(1))
    expect(writes('PATCH')[0].url).toBe('/api/exercises/1')
    expect(writes('PATCH')[0].body).toMatchObject({ stage_id: null, topic_ids: [10] })
  })
})

describe('the drill form', () => {
  it('adds a drill to the exercise it was opened from, with source links and resources apart', async () => {
    handler = (call) => (call.method === 'POST' ? json({ ...DRILL, id: 6 }, 201) : null)
    renderAt('/drills/new?exercise=1')
    const exercise = screen.getByRole('combobox', { name: '練習項目' })
    await waitFor(() => expect(exercise.value).toBe('1'))
    fireEvent.change(screen.getByRole('textbox', { name: /名稱/ }), { target: { value: '綜合線條' } })
    fireEvent.click(await screen.findByRole('button', { name: '自訂' }))
    fireEvent.change(screen.getByRole('textbox', { name: /單位/ }), { target: { value: '組' } })
    fireEvent.change(screen.getByRole('spinbutton', { name: /目標/ }), { target: { value: '50' } })
    fireEvent.change(screen.getByRole('spinbutton', { name: '建議分鐘' }), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: /新增來源連結/ }))
    fireEvent.change(screen.getByRole('textbox', { name: '來源連結 1 連結' }), { target: { value: 'https://c.example' } })
    fireEvent.click(screen.getByRole('button', { name: /新增資源/ }))
    fireEvent.change(screen.getByRole('textbox', { name: '資源 1 連結' }), { target: { value: 'https://r.example' } })

    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(currentLocation()).toBe('/drills/6'))
    expect(writes('POST')[0].url).toBe('/api/drills')
    expect(writes('POST')[0].body).toEqual({
      exercise_id: 1,
      name: '綜合線條',
      source_id: 20,
      unit: '組',
      target: 50,
      suggested_minutes: 10,
      frequency: null,
      instructions: null,
      source_links: [{ name: null, url: 'https://c.example' }],
      resources: [{ name: null, url: 'https://r.example' }],
      remark: null,
    })
  })
})
