// The record pages through the real routes, with fetch mocked: the log
// groups by day, newest first, with each day's minutes and this week's total
// from the summary; its filters live in the URL; the form fills today, the
// newest record's location and Clip Studio Paint, and sends a drill or an
// exercise - never both - and a test's one stage or level.
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { localToday } from '../lib/roadmap'
import { weekRange } from '../lib/records'
import { currentLocation, json, renderAt, stubFetch } from './pageHarness'

const option = (id, category, value, description = null) => ({
  id,
  category,
  value,
  description,
  remark: null,
  sort_order: 0,
  in_use: 0,
})
const ref = ({ id, value, description }) => ({ id, value, description })

const LOCATIONS = [option(30, 'location', '台灣・家'), option(31, 'location', '美國・家')]
// Clip Studio Paint is deliberately not first: a default taken from the
// first option would pass for the wrong reason.
const TOOLS = [option(40, 'tool', 'Procreate'), option(41, 'tool', 'Clip Studio Paint'), option(42, 'tool', '紙筆')]
const METHODS = [option(50, 'method', '臨摹', '照著參考畫'), option(51, 'method', '速寫', '限時抓大形')]

const LINES = { id: 1, display_name: '線條' }
const DRILL_REF = { id: 5, display_name: '基本線條' }

const record = (fields) => ({
  location: null,
  duration_minutes: null,
  activity: null,
  kind: 'practice',
  stage: null,
  goal: null,
  method: null,
  tool: null,
  references: [],
  notes: null,
  ...fields,
})

// Newest first, as the server sends them. The newest record is in 美國・家,
// the SECOND location, so the location default is not the first option.
const RECORDS = [
  record({
    id: 3,
    date: '2026-10-02',
    duration_minutes: 30,
    location: ref(LOCATIONS[1]),
    activity: { exercise: LINES, drill: DRILL_REF },
    tool: ref(TOOLS[1]),
    notes: '手腕太用力',
  }),
  record({ id: 2, date: '2026-10-02', duration_minutes: null, activity: { exercise: LINES, drill: null } }),
  record({ id: 4, date: '2026-10-02', duration_minutes: 15, kind: 'piece' }),
  record({
    id: 1,
    date: '2026-09-30',
    duration_minutes: 60,
    kind: 'test',
    goal: { id: 1, code: 'L0', display_name: '基礎' },
    activity: { exercise: LINES, drill: null },
  }),
]

const SUMMARY = [
  { date: '2026-09-30', minutes: 60, records: 1 },
  { date: '2026-10-02', minutes: 45, records: 3 },
]

const EXERCISES = [
  { id: 1, display_name: '線條', stage: null, topics: [], drill_count: 1, record_count: 3, total_minutes: 90 },
  { id: 2, display_name: '動態速寫', stage: null, topics: [], drill_count: 0, record_count: 0, total_minutes: 0 },
]

const EXERCISE = {
  ...EXERCISES[0],
  drills: [{ id: 5, exercise: LINES, display_name: '基本線條' }, { id: 6, exercise: LINES, display_name: '綜合線條' }],
}

const GOALS = [
  {
    id: 1,
    code: 'L0',
    display_name: '基礎',
    stages: [{ id: 11, number: 1, display_name: '線條與形狀' }],
  },
]

let calls
let handler

function defaultResponse(call) {
  const [path, query = ''] = call.url.split('?')
  if (path === '/api/options') {
    if (query.includes('category=location')) return json(LOCATIONS)
    if (query.includes('category=tool')) return json(TOOLS)
    if (query.includes('category=method')) return json(METHODS)
    return json([])
  }
  if (path === '/api/records/summary') return json(SUMMARY)
  if (path === '/api/records') return json(RECORDS)
  if (path === '/api/records/3') return json(RECORDS[0])
  if (path === '/api/records/1') return json(RECORDS[3])
  if (path === '/api/exercises') return json(EXERCISES)
  if (path === '/api/exercises/1') return json(EXERCISE)
  if (path === '/api/drills/5') return json({ ...EXERCISE.drills[0], name: '基本線條' })
  if (path === '/api/goals') return json(GOALS)
  return json([])
}

const writes = (method) => calls.filter((call) => call.method === method)
const pressed = (group) =>
  within(screen.getByRole('group', { name: group }))
    .getAllByRole('button')
    .filter((button) => button.getAttribute('aria-pressed') === 'true')
    .map((button) => button.textContent)

beforeEach(() => {
  handler = () => null
  calls = stubFetch((call) => handler(call) ?? defaultResponse(call))
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('the record log', () => {
  it('groups by day, newest first, with each day’s minutes and this week’s total', async () => {
    renderAt('/records')
    const newest = await screen.findByRole('list', { name: '2026-10-02' })
    const days = screen.getAllByRole('heading', { level: 2 }).map((heading) => heading.textContent)
    expect(days).toEqual(['2026-10-02（五）', '2026-09-30（三）'])

    // 30 + none + 15: a record with no duration counts, as zero.
    const newestDay = newest.closest('section')
    expect(within(newestDay).getByText('共 45 分鐘')).toBeTruthy()
    expect(within(newest).getAllByRole('listitem')).toHaveLength(3)
    const oldest = screen.getByRole('list', { name: '2026-09-30' }).closest('section')
    expect(within(oldest).getByText('共 60 分鐘')).toBeTruthy()

    // The drill's own name, the kind when it is not practice, a test's level.
    expect(within(newest).getByText('基本線條')).toBeTruthy()
    expect(within(newest).getByText('作品')).toBeTruthy()
    expect(within(newest).getAllByRole('link', { name: '編輯 2026-10-02 的紀錄' })[0]).toBeTruthy()
    expect(screen.getByText('L0 基礎')).toBeTruthy()

    expect((await screen.findByTestId('week-minutes')).textContent).toBe('105')
    const week = weekRange()
    expect(calls.some((call) => call.url === `/api/records/summary?from=${week.from}&to=${week.to}`)).toBe(true)
  })

  it('keeps the kind and exercise filters in the URL and sends them to the API', async () => {
    renderAt('/records?kind=test&exercise=1')
    await screen.findByRole('list', { name: '2026-10-02' })
    expect(calls.some((call) => call.url === '/api/records?kind=test&exercise_id=1')).toBe(true)

    fireEvent.click(screen.getAllByRole('button', { name: '作品' })[0])
    await waitFor(() => expect(currentLocation()).toBe('/records?kind=piece&exercise=1'))
  })
})

describe('the record form', () => {
  it('fills today, the newest record’s location and Clip Studio Paint, and sends a drill alone', async () => {
    handler = (call) => (call.method === 'POST' ? json({ ...RECORDS[0], id: 9 }, 201) : null)
    renderAt('/records/new?drill=5')

    expect(screen.getByLabelText('日期').value).toBe(localToday())
    await waitFor(() => expect(pressed('地點')).toEqual(['美國・家']))
    await waitFor(() => expect(pressed('工具')).toEqual(['Clip Studio Paint']))

    // The drill brings its exercise, and is chosen within it.
    const exercise = screen.getByRole('combobox', { name: '練習項目' })
    await waitFor(() => expect(exercise.value).toBe('1'))
    const drill = screen.getByRole('combobox', { name: /練法/ })
    await waitFor(() => expect(drill.value).toBe('5'))

    fireEvent.change(screen.getByRole('spinbutton', { name: /分鐘/ }), { target: { value: '20' } })
    fireEvent.click(screen.getByRole('button', { name: '速寫' }))
    expect(screen.getByText('限時抓大形')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(currentLocation()).toBe('/records'))
    expect(writes('POST')[0].url).toBe('/api/records')
    expect(writes('POST')[0].body).toEqual({
      date: localToday(),
      location_id: 31,
      duration_minutes: 20,
      drill_id: 5,
      exercise_id: null,
      kind: 'practice',
      stage_id: null,
      goal_id: null,
      method_id: 51,
      tool_id: 41,
      references: [],
      notes: null,
    })
  })

  it('sends an exercise alone, and a test with exactly one level', async () => {
    handler = (call) => (call.method === 'POST' ? json({ ...RECORDS[3], id: 9 }, 201) : null)
    renderAt('/records/new?exercise=1')
    await waitFor(() => expect(screen.getByRole('combobox', { name: '練習項目' }).value).toBe('1'))
    // Clearing a default sticks.
    fireEvent.click(await screen.findByRole('button', { name: 'Clip Studio Paint' }))
    expect(pressed('工具')).toEqual([])

    fireEvent.change(screen.getByRole('combobox', { name: '類型' }), { target: { value: 'test' } })
    // A test with nothing chosen is refused here, before the server.
    await waitFor(() => expect(screen.getByRole('button', { name: '儲存' }).disabled).toBe(false))
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    expect(await screen.findByText('測驗要選一個階段或一個等級。')).toBeTruthy()
    expect(writes('POST')).toHaveLength(0)

    const target = screen.getByRole('combobox', { name: /測驗對象/ })
    expect(within(target).getAllByRole('option').map((o) => o.value)).toEqual(['', 'goal:1', 'stage:11'])
    fireEvent.change(target, { target: { value: 'goal:1' } })
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(writes('POST')).toHaveLength(1))
    expect(writes('POST')[0].body).toMatchObject({
      drill_id: null,
      exercise_id: 1,
      kind: 'test',
      stage_id: null,
      goal_id: 1,
      location_id: 31,
      tool_id: null,
    })
  })

  it('edits a record as it was saved, and deletes it', async () => {
    handler = (call) => {
      if (call.method === 'PATCH') return json(RECORDS[0])
      if (call.method === 'DELETE') return json(null, 204)
      return null
    }
    renderAt('/records/3/edit')
    await waitFor(() => expect(screen.getByRole('combobox', { name: /練法/ }).value).toBe('5'))
    expect(screen.getByLabelText('日期').value).toBe('2026-10-02')
    expect(pressed('地點')).toEqual(['美國・家'])
    expect(calls.some((call) => call.url === '/api/records')).toBe(false)

    // Choosing another exercise drops the drill: the record names the exercise.
    fireEvent.change(screen.getByRole('combobox', { name: '練習項目' }), { target: { value: '2' } })
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(writes('PATCH')).toHaveLength(1))
    expect(writes('PATCH')[0].url).toBe('/api/records/3')
    expect(writes('PATCH')[0].body).toMatchObject({ drill_id: null, exercise_id: 2, date: '2026-10-02', notes: '手腕太用力' })
  })
})
