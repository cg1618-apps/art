// The roadmap pages through the real routes, with fetch mocked: the roadmap
// draws every goal and its stages and marks the current stage; a status
// change and a move send the PATCH bodies; the goal form shows the server's
// 409 when a goal with stages is deleted; the stage form and page, with the
// stage's exercises and test records.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { localToday } from '../../lib/roadmap'
import AppRoutes from '../../routes'

const stage = (fields) => ({
  name_cn: null,
  name_en: null,
  name_alt: null,
  description: null,
  test: null,
  status: 'not_started',
  passed_on: null,
  ...fields,
  display_name: fields.name_cn,
})

// The first goal's first stage is passed, so the current stage is the
// SECOND row - a first-row highlight would not pass for the right reason.
const GOALS = [
  {
    id: 1,
    code: 'L0',
    display_name: '基礎',
    name_cn: '基礎',
    name_en: 'Foundations',
    name_alt: null,
    position: 0,
    description: '能穩定地畫出線條與基本形狀。',
    test: '20 個方塊。',
    status: 'active',
    achieved_on: null,
    remark: null,
    stages: [
      stage({ id: 10, number: 0, position: 0, name_cn: '設定', status: 'passed', passed_on: '2026-10-01' }),
      stage({ id: 11, number: 1, position: 1, name_cn: '線條與形狀', test: '一頁穩定的線條。' }),
      stage({ id: 12, number: 2, position: 2, name_cn: '空間中的形體' }),
    ],
  },
  {
    id: 2,
    code: 'L1',
    display_name: '人體',
    name_cn: '人體',
    name_en: 'Figure',
    name_alt: null,
    position: 1,
    description: null,
    test: null,
    status: 'planned',
    achieved_on: null,
    remark: null,
    stages: [stage({ id: 20, number: 3, position: 0, name_cn: '比例' })],
  },
]

const STAGE = {
  ...GOALS[0].stages[1],
  goal: { id: 1, code: 'L0', display_name: '基礎' },
  remark: '慢慢來',
  resources: [{ id: 1, name: '講座', url: 'https://example.com/lines' }],
}

const STAGE_EXERCISES = [
  { id: 1, display_name: '線條', stage: { id: 11, number: 1, display_name: '線條與形狀' }, drill_count: 2, total_minutes: 50 },
]

const TEST_RECORDS = [
  {
    id: 70,
    date: '2026-10-02',
    location: null,
    duration_minutes: 45,
    activity: { exercise: { id: 1, display_name: '線條' }, drill: null },
    kind: 'test',
    stage: { id: 11, number: 1, display_name: '線條與形狀' },
    goal: null,
    method: null,
    tool: null,
    references: [],
    notes: '一頁都穩了',
  },
]

let calls
let handler

function json(body, status = 200) {
  return new Response(body === null ? null : JSON.stringify(body), { status })
}

function defaultResponse(call) {
  const path = call.url.split('?')[0]
  if (path === '/api/goals') return json(GOALS)
  if (path === '/api/goals/1') return json(GOALS[0])
  if (path === '/api/stages/11') return json(STAGE)
  if (path === '/api/exercises') return json(STAGE_EXERCISES)
  if (path === '/api/records') return json(TEST_RECORDS)
  return json([])
}

function LocationProbe() {
  const { pathname, search } = useLocation()
  return <output data-testid="location">{`${pathname}${search}`}</output>
}

function renderAt(path) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const location = () => screen.getByTestId('location').textContent
const writes = (method) => calls.filter((call) => call.method === method)

beforeEach(() => {
  calls = []
  handler = () => null
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options = {}) => {
      const call = {
        url: decodeURIComponent(url),
        method: options.method ?? 'GET',
        body: typeof options.body === 'string' ? JSON.parse(options.body) : undefined,
      }
      calls.push(call)
      return handler(call) ?? defaultResponse(call)
    }),
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('routing', () => {
  it('sends / to the roadmap, first in the navigation', async () => {
    renderAt('/')
    expect(await screen.findByRole('heading', { level: 1, name: '路線圖' })).toBeTruthy()
    expect(location()).toBe('/roadmap')
    const nav = screen.getAllByRole('navigation', { name: '主要' })[0]
    const links = within(nav).getAllByRole('link').map((link) => link.textContent)
    expect(links.slice(1)).toEqual(['路線圖', '練習', '紀錄', '計時', '筆記', '選項'])
  })
})

describe('the roadmap', () => {
  it('draws every goal with its stages, and marks the first stage not passed', async () => {
    renderAt('/roadmap')
    const l0 = await screen.findByRole('region', { name: '基礎' })
    expect(within(l0).getByText('L0')).toBeTruthy()
    expect(within(l0).getByText('進行中', { selector: 'span' })).toBeTruthy()
    expect(within(l0).getByText('能穩定地畫出線條與基本形狀。')).toBeTruthy()
    expect(within(l0).getByText('20 個方塊。')).toBeTruthy()

    const rows = within(within(l0).getByRole('list', { name: '基礎的階段' })).getAllByRole('listitem')
    expect(rows).toHaveLength(3)
    expect(within(rows[1]).getByRole('link', { name: '線條與形狀' }).getAttribute('href')).toBe('/roadmap/stages/11')
    expect(rows[1].textContent).toContain('一頁穩定的線條。')

    // The mark is on the second row, and on no other row on the page.
    expect(rows[1].getAttribute('aria-current')).toBe('step')
    const marked = document.querySelectorAll('[aria-current="step"]')
    expect(marked).toHaveLength(1)
    expect(rows[0].getAttribute('aria-current')).toBeNull()

    const l1 = screen.getByRole('region', { name: '人體' })
    expect(within(l1).getByText('計畫中')).toBeTruthy()
    expect(within(l1).getByRole('link', { name: /新增階段/ }).getAttribute('href')).toBe('/roadmap/stages/new?goal=2')
  })

  it('sends passed with today as the date, and any other status alone', async () => {
    handler = (call) => (call.method === 'PATCH' ? json({}) : null)
    renderAt('/roadmap')
    const select = await screen.findByRole('combobox', { name: '「線條與形狀」的狀態' })
    expect(select.value).toBe('not_started')

    fireEvent.change(select, { target: { value: 'passed' } })
    await waitFor(() => expect(writes('PATCH')).toHaveLength(1))
    expect(writes('PATCH')[0]).toMatchObject({
      url: '/api/stages/11',
      body: { status: 'passed', passed_on: localToday() },
    })

    await waitFor(() => expect(select.disabled).toBe(false))
    fireEvent.change(select, { target: { value: 'in_progress' } })
    await waitFor(() => expect(writes('PATCH')).toHaveLength(2))
    expect(writes('PATCH')[1].body).toEqual({ status: 'in_progress' })
  })

  it('moves a stage up inside its goal by PATCHing the positions that changed', async () => {
    handler = (call) => (call.method === 'PATCH' ? json({}) : null)
    renderAt('/roadmap')
    expect((await screen.findByRole('button', { name: '上移「設定」' })).disabled).toBe(true)
    expect(screen.getByRole('button', { name: '下移「空間中的形體」' }).disabled).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: '上移「空間中的形體」' }))
    await waitFor(() => expect(writes('PATCH')).toHaveLength(2))
    expect(writes('PATCH').map(({ url, body }) => ({ url, body }))).toEqual([
      { url: '/api/stages/12', body: { position: 1 } },
      { url: '/api/stages/11', body: { position: 2 } },
    ])
  })

  it('shows a refused status change on its row', async () => {
    handler = (call) => (call.method === 'PATCH' ? json({ detail: '日期不對。' }, 422) : null)
    renderAt('/roadmap')
    fireEvent.change(await screen.findByRole('combobox', { name: '「比例」的狀態' }), {
      target: { value: 'passed' },
    })
    expect(await screen.findByText('日期不對。')).toBeTruthy()
  })
})

describe('the goal form', () => {
  it('shows the date only when achieved, filled with today, and sends it', async () => {
    handler = (call) => (call.method === 'POST' ? json({ ...GOALS[1], id: 3 }, 201) : null)
    renderAt('/roadmap/goals/new')
    fireEvent.change(screen.getByRole('textbox', { name: /代號/ }), { target: { value: ' L6 ' } })
    fireEvent.change(screen.getByRole('textbox', { name: '中文名' }), { target: { value: '動畫' } })
    expect(screen.queryByLabelText('達成日期')).toBeNull()

    fireEvent.change(screen.getByRole('combobox', { name: '狀態' }), { target: { value: 'achieved' } })
    expect(screen.getByLabelText('達成日期').value).toBe(localToday())

    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(location()).toBe('/roadmap'))
    expect(writes('POST')[0]).toMatchObject({ url: '/api/goals' })
    expect(writes('POST')[0].body).toEqual({
      code: 'L6',
      name_cn: '動畫',
      name_en: null,
      name_alt: null,
      description: null,
      test: null,
      status: 'achieved',
      achieved_on: localToday(),
      remark: null,
    })
  })

  it('shows the server refusing to delete a goal that has stages, and stays', async () => {
    handler = (call) =>
      call.method === 'DELETE' ? json({ detail: '這個等級還有 3 個階段，不能刪除。', stages: 3 }, 409) : null
    renderAt('/roadmap/goals/1/edit')
    expect(await screen.findByDisplayValue('Foundations')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '刪除' }))
    const dialog = screen.getByRole('dialog')
    expect(dialog.textContent).toContain('3 個階段')
    fireEvent.click(within(dialog).getByRole('button', { name: '刪除' }))

    expect(await within(dialog).findByText('這個等級還有 3 個階段，不能刪除。')).toBeTruthy()
    expect(writes('DELETE')[0].url).toBe('/api/goals/1')
    expect(location()).toBe('/roadmap/goals/1/edit')
  })
})

describe('a stage', () => {
  it('shows its goal, status, test, resources and remark', async () => {
    renderAt('/roadmap/stages/11')
    expect(await screen.findByRole('heading', { level: 1, name: '線條與形狀' })).toBeTruthy()
    expect(screen.getByText('階段 1')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'L0 基礎' }).getAttribute('href')).toBe('/roadmap')
    expect(screen.getByText('未開始')).toBeTruthy()
    expect(screen.getByText('一頁穩定的線條。')).toBeTruthy()
    expect(screen.getByRole('link', { name: /講座/ }).getAttribute('href')).toBe('https://example.com/lines')
    expect(screen.getByText('慢慢來')).toBeTruthy()
  })

  it('lists its exercises and its test records, each linked', async () => {
    renderAt('/roadmap/stages/11')
    const exercises = await screen.findByRole('list', { name: '這個階段的練習' })
    expect(within(exercises).getByRole('link', { name: '線條' }).getAttribute('href')).toBe('/exercises/1')
    expect(within(exercises).getByText('2 個練法 · 50 分鐘')).toBeTruthy()

    const tests = await screen.findByRole('list', { name: '這個階段的測驗紀錄' })
    expect(within(tests).getByText('一頁都穩了')).toBeTruthy()
    expect(within(tests).getByRole('link', { name: '編輯 2026-10-02 的紀錄' }).getAttribute('href')).toBe(
      '/records/70/edit',
    )
    expect(calls.some((call) => call.url === '/api/exercises?stage_id=11')).toBe(true)
    expect(calls.some((call) => call.url === '/api/records?stage_id=11&kind=test')).toBe(true)
  })

  it('adds a stage to the goal it was opened from, with its resources', async () => {
    handler = (call) => (call.method === 'POST' ? json({ ...STAGE, id: 30 }, 201) : null)
    renderAt('/roadmap/stages/new?goal=2')
    const goal = screen.getByRole('combobox', { name: '等級' })
    await waitFor(() => expect(goal.value).toBe('2'))
    fireEvent.change(screen.getByRole('textbox', { name: '英文名' }), { target: { value: 'Gesture' } })
    fireEvent.click(screen.getByRole('button', { name: /新增資源/ }))
    fireEvent.change(screen.getByRole('textbox', { name: '資源 1 連結' }), { target: { value: 'https://g.example' } })

    fireEvent.click(await screen.findByRole('button', { name: '儲存' }))
    await waitFor(() => expect(location()).toBe('/roadmap/stages/30'))
    expect(writes('POST')[0].body).toEqual({
      goal_id: 2,
      name_cn: null,
      name_en: 'Gesture',
      name_alt: null,
      description: null,
      test: null,
      status: 'not_started',
      remark: null,
      resources: [{ name: null, url: 'https://g.example' }],
    })
  })

  it('moving a stage to another goal does not carry its old position', async () => {
    handler = (call) => (call.method === 'PATCH' ? json(STAGE) : null)
    renderAt('/roadmap/stages/11/edit')
    expect(await screen.findByDisplayValue('線條與形狀')).toBeTruthy()
    const goal = screen.getByRole('combobox', { name: '等級' })
    await waitFor(() => expect(goal.value).toBe('1'))
    fireEvent.change(goal, { target: { value: '2' } })
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(location()).toBe('/roadmap/stages/11'))
    const patch = writes('PATCH')[0]
    expect(patch.url).toBe('/api/stages/11')
    expect(patch.body.goal_id).toBe(2)
    expect('position' in patch.body).toBe(false)
    expect(patch.body.resources).toEqual([{ name: '講座', url: 'https://example.com/lines' }])
  })
})
