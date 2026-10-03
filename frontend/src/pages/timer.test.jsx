// The timer through the real routes, with fetch mocked and a fake server
// holding one timer: the start form defaults by the day of the week and sends
// a countdown with its drill; the live figure follows the server's clock, not
// the browser's; the tone plays once at zero and not on opening a page already
// past it; 停止 opens the record form prefilled, whose save is
// /api/timer/record; the chip in the top bar; 捨棄; a drill's 開始計時.
import { act, cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { currentLocation, json, renderAt, stubFetch } from './pageHarness'

const LINES = { id: 1, display_name: '線條' }
const DRILL_REF = { id: 5, display_name: '基本線條' }
const DRILL = { id: 5, exercise: LINES, name: '基本線條', display_name: '基本線條' }
const EXERCISES = [
  { id: 1, display_name: '線條', stage: null, topics: [], drill_count: 1, record_count: 0, total_minutes: 0 },
]
const EXERCISE = { ...EXERCISES[0], aliases: [], resources: [], drills: [DRILL] }

// The server's clock in these tests. The browser's is set apart from it where
// that matters.
const SERVER_NOW = Date.parse('2026-10-03T10:00:00Z')
const iso = (ms) => new Date(ms).toISOString()

const timer = (fields) => ({
  id: 7,
  mode: 'countdown',
  target_seconds: 600,
  state: 'running',
  started_at: iso(SERVER_NOW - 120_000),
  running_since: iso(SERVER_NOW - 120_000),
  elapsed_seconds: 0,
  stopped_at: null,
  now: iso(SERVER_NOW),
  activity: { exercise: LINES, drill: DRILL_REF },
  ...fields,
})

let calls
let server
let handler

function respond(call) {
  const [path] = call.url.split('?')
  if (path === '/api/timer' && call.method === 'GET') return json(server)
  if (path === '/api/timer' && call.method === 'POST') {
    if (server) return json({ detail: '已經有一個計時。' }, 409)
    server = timer({ ...call.body, id: 8, elapsed_seconds: 0, running_since: iso(SERVER_NOW), started_at: iso(SERVER_NOW) })
    return json(server, 201)
  }
  if (path === '/api/timer' && call.method === 'DELETE') {
    server = null
    return json(null, 204)
  }
  if (path === '/api/timer/pause') {
    server = { ...server, state: 'paused', running_since: null, elapsed_seconds: 130 }
    return json(server)
  }
  if (path === '/api/timer/stop') {
    server = { ...server, state: 'stopped', running_since: null, elapsed_seconds: 1250, stopped_at: iso(SERVER_NOW) }
    return json(server)
  }
  if (path === '/api/timer/record') {
    server = null
    return json({ id: 99, date: call.body.date }, 201)
  }
  if (path === '/api/exercises') return json(EXERCISES)
  if (path === '/api/exercises/1') return json(EXERCISE)
  if (path === '/api/drills/5') return json(DRILL)
  if (path === '/api/options' && call.url.includes('category=tool')) {
    return json([{ id: 41, category: 'tool', value: 'Clip Studio Paint', description: null, sort_order: 0, in_use: 0 }])
  }
  return json([])
}

const writes = (method) => calls.filter((call) => call.method === method)
const clock = () => screen.getByRole('timer', { name: '計時' }).textContent
// Lets fetches resolve and fake timers run, `ms` of them.
const advance = (ms = 0) => act(() => vi.advanceTimersByTimeAsync(ms))

let tones
class FakeAudioContext {
  currentTime = 0
  destination = {}
  constructor() {
    tones += 1
  }
  createOscillator() {
    return { frequency: { setValueAtTime() {} }, connect() {}, start() {}, stop() {} }
  }
  createGain() {
    return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }
  }
}

beforeEach(() => {
  server = null
  handler = () => null
  tones = 0
  calls = stubFetch((call) => handler(call) ?? respond(call))
  vi.stubGlobal('AudioContext', FakeAudioContext)
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.unstubAllGlobals()
  document.title = 'art'
})

describe('the start form', () => {
  it('defaults to 30 minutes at the weekend and sends a countdown with its drill', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 9, 3, 12, 0)) // a Saturday
    renderAt('/timer?drill=5')

    const minutes = await screen.findByRole('spinbutton', { name: '分鐘' })
    expect(minutes.value).toBe('30')
    const pressed = within(screen.getByRole('group', { name: '預設' }))
      .getAllByRole('button')
      .filter((button) => button.getAttribute('aria-pressed') === 'true')
    expect(pressed.map((button) => button.textContent)).toEqual(['30 分鐘'])
    await waitFor(() => expect(screen.getByRole('combobox', { name: /練法/ }).value).toBe('5'))
    expect(screen.getByRole('combobox', { name: '練習項目' }).value).toBe('1')

    fireEvent.click(screen.getByRole('button', { name: '開始' }))
    await waitFor(() => expect(writes('POST')).toHaveLength(1))
    expect(writes('POST')[0]).toMatchObject({
      url: '/api/timer',
      body: { mode: 'countdown', target_seconds: 1800, drill_id: 5 },
    })
    expect(await screen.findByRole('timer', { name: '計時' })).toBeTruthy()
  })

  it('defaults to 10 minutes on a weekday; a stopwatch sends no target', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 8, 30, 12, 0)) // a Wednesday
    renderAt('/timer?exercise=1')

    expect((await screen.findByRole('spinbutton', { name: '分鐘' })).value).toBe('10')
    fireEvent.click(screen.getByRole('button', { name: '碼錶' }))
    expect(screen.queryByRole('spinbutton', { name: '分鐘' })).toBeNull()
    await waitFor(() => expect(screen.getByRole('combobox', { name: '練習項目' }).value).toBe('1'))

    fireEvent.click(screen.getByRole('button', { name: '開始' }))
    await waitFor(() => expect(writes('POST')).toHaveLength(1))
    expect(writes('POST')[0].body).toEqual({ mode: 'stopwatch', exercise_id: 1 })
  })
})

describe('the running timer', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date', 'setTimeout', 'clearTimeout', 'setInterval', 'clearInterval'] })
  })

  it('counts from the server’s clock, and ticks', async () => {
    // The browser is an hour behind the server: by its own clock the timer
    // would not have started yet.
    vi.setSystemTime(SERVER_NOW - 3_600_000)
    server = timer({ mode: 'stopwatch', target_seconds: null, running_since: iso(SERVER_NOW - 60_000), elapsed_seconds: 15 })
    renderAt('/timer')
    await advance()
    expect(clock()).toBe('1:15')
    await advance(2000)
    expect(clock()).toBe('1:17')
    expect(document.title).toBe('▶ 1:17 · art')
  })

  it('plays the tone once when a countdown reaches zero, and keeps counting', async () => {
    vi.setSystemTime(SERVER_NOW)
    server = timer({ running_since: iso(SERVER_NOW - 598_000) })
    renderAt('/timer')
    await advance()
    expect(clock()).toBe('0:02')
    expect(tones).toBe(0)

    await advance(3000)
    expect(clock()).toBe('+0:01')
    expect(tones).toBe(1)
    expect(document.title).toBe('+0:01 · art')

    await advance(5000)
    expect(clock()).toBe('+0:06')
    expect(tones).toBe(1)
  })

  it('does not play it on opening a page already past zero', async () => {
    vi.setSystemTime(SERVER_NOW)
    server = timer({ running_since: iso(SERVER_NOW - 700_000) })
    renderAt('/timer')
    await advance()
    expect(clock()).toBe('+1:40')
    await advance(3000)
    expect(clock()).toBe('+1:43')
    // Past the 30 s refetch too: a fresh read of the same timer is not a crossing.
    const reads = calls.filter((call) => call.url === '/api/timer').length
    await advance(31_000)
    expect(calls.filter((call) => call.url === '/api/timer').length).toBeGreaterThan(reads)
    expect(tones).toBe(0)
  })
})

describe('stopping', () => {
  it('opens the record form prefilled, and saves through /api/timer/record', async () => {
    server = timer({})
    renderAt('/timer')
    fireEvent.click(await screen.findByRole('button', { name: '停止' }))

    await waitFor(() => expect(currentLocation()).toBe('/records/new?from=timer'))
    expect(writes('POST')[0].url).toBe('/api/timer/stop')
    // 1250 s is 20.8 minutes: the nearest minute.
    await waitFor(() => expect(screen.getByRole('spinbutton', { name: /分鐘/ }).value).toBe('21'))
    const started = new Date(SERVER_NOW - 120_000)
    const pad = (n) => String(n).padStart(2, '0')
    const startedDate = `${started.getFullYear()}-${pad(started.getMonth() + 1)}-${pad(started.getDate())}`
    expect(screen.getByLabelText('日期').value).toBe(startedDate)
    await waitFor(() => expect(screen.getByRole('combobox', { name: /練法/ }).value).toBe('5'))
    expect(screen.queryByText(/超過 3 小時/)).toBeNull()

    // While the record is owed, the top bar says so.
    expect(screen.getByRole('link', { name: /待記錄/ }).getAttribute('href')).toBe('/records/new?from=timer')

    const save = screen.getByRole('button', { name: '儲存' })
    await waitFor(() => expect(save.disabled).toBe(false))
    fireEvent.click(save)
    await waitFor(() => expect(currentLocation()).toBe('/records'))
    const posted = writes('POST').filter((call) => call.url === '/api/timer/record')
    expect(posted).toHaveLength(1)
    expect(posted[0].body).toMatchObject({
      date: startedDate,
      duration_minutes: 21,
      drill_id: 5,
      exercise_id: null,
      kind: 'practice',
      tool_id: 41,
    })
    expect(writes('POST').some((call) => call.url === '/api/records')).toBe(false)
    await waitFor(() => expect(screen.queryByRole('link', { name: /待記錄/ })).toBeNull())
  })

  it('asks for the minutes to be checked after more than three hours', async () => {
    server = timer({ state: 'stopped', running_since: null, elapsed_seconds: 3 * 3600 + 125, stopped_at: iso(SERVER_NOW) })
    renderAt('/records/new?from=timer')
    expect(await screen.findByText(/計時了 3:02:05，超過 3 小時/)).toBeTruthy()
    expect(screen.getByRole('spinbutton', { name: /分鐘/ }).value).toBe('182')

    // Leaving keeps it stopped: 取消 goes to /timer, which offers 記錄 again.
    fireEvent.click(screen.getByRole('button', { name: '取消' }))
    await waitFor(() => expect(currentLocation()).toBe('/timer'))
    expect(screen.getByRole('link', { name: '記錄' }).getAttribute('href')).toBe('/records/new?from=timer')
    expect(writes('DELETE')).toHaveLength(0)
  })

  it('has nothing to record without a stopped timer', async () => {
    renderAt('/records/new?from=timer')
    expect(await screen.findByText('沒有待記錄的計時。')).toBeTruthy()
  })
})

describe('the top bar chip', () => {
  it('shows on every page while a timer exists, and pauses it', async () => {
    server = timer({ state: 'paused', running_since: null, elapsed_seconds: 138 })
    renderAt('/records')
    const chip = await screen.findByRole('link', { name: /基本線條\s*7:42/ })
    expect(chip.getAttribute('href')).toBe('/timer')
    expect(document.title).toBe('⏸ 7:42 · art')

    server = { ...server, state: 'running', running_since: iso(Date.now()) }
    handler = (call) => (call.url === '/api/timer/resume' ? json(server) : null)
    fireEvent.click(screen.getByRole('button', { name: '繼續計時' }))
    await waitFor(() => expect(writes('POST').map((call) => call.url)).toEqual(['/api/timer/resume']))
    expect(await screen.findByRole('button', { name: '暫停計時' })).toBeTruthy()
  })

  it('is not there without a timer', async () => {
    renderAt('/records')
    await waitFor(() => expect(calls.some((call) => call.url === '/api/timer')).toBe(true))
    expect(screen.queryByRole('button', { name: /計時$/ })).toBeNull()
    expect(document.title).toBe('art')
  })
})

describe('捨棄', () => {
  it('asks first, then deletes the timer', async () => {
    server = timer({ state: 'paused', running_since: null, elapsed_seconds: 30 })
    renderAt('/timer')
    fireEvent.click(await screen.findByRole('button', { name: '捨棄' }))
    const dialog = screen.getByRole('dialog', { name: '捨棄這次計時？' })
    fireEvent.click(within(dialog).getByRole('button', { name: '保留' }))
    expect(writes('DELETE')).toHaveLength(0)

    fireEvent.click(screen.getByRole('button', { name: '捨棄' }))
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: '捨棄' }))
    await waitFor(() => expect(writes('DELETE').map((call) => call.url)).toEqual(['/api/timer']))
    expect(await screen.findByRole('button', { name: '開始' })).toBeTruthy()
  })
})

describe('a drill’s 開始計時', () => {
  it('starts the day’s countdown with the drill and goes to /timer', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 9, 5, 12, 0)) // a Monday
    renderAt('/exercises/1')
    fireEvent.click(await screen.findByRole('button', { name: '為「基本線條」開始計時' }))
    await waitFor(() => expect(currentLocation()).toBe('/timer'))
    expect(writes('POST')[0]).toMatchObject({
      url: '/api/timer',
      body: { mode: 'countdown', target_seconds: 600, drill_id: 5 },
    })
  })

  it('only goes to /timer when one is already running', async () => {
    server = timer({})
    renderAt('/exercises/1')
    await screen.findByRole('link', { name: /基本線條\s*\d/ })
    fireEvent.click(await screen.findByRole('button', { name: '為「基本線條」開始計時' }))
    await waitFor(() => expect(currentLocation()).toBe('/timer'))
    expect(writes('POST')).toHaveLength(0)
  })
})
