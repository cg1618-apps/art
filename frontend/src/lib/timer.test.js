import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  asTimer,
  clockOffset,
  defaultCountdownMinutes,
  formatClock,
  isLongTimer,
  liveSeconds,
  playTone,
  roundToMinutes,
  startPayload,
  timerClock,
  timerRecordForm,
  timerTitle,
  validMinutes,
} from './timer'

const timer = (fields) => ({
  id: 1,
  mode: 'stopwatch',
  target_seconds: null,
  state: 'running',
  started_at: '2026-10-03T10:00:00Z',
  running_since: '2026-10-03T10:00:00Z',
  elapsed_seconds: 0,
  stopped_at: null,
  now: '2026-10-03T10:00:00Z',
  activity: null,
  ...fields,
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('the live figure', () => {
  it('counts from the server’s clock, not the browser’s', () => {
    // The browser is an hour behind the server. Measured against its own
    // clock the timer would have run -59 minutes; against the offset, 90 s.
    const serverNow = Date.parse('2026-10-03T10:01:30Z')
    const browserNow = serverNow - 3_600_000
    const running = timer({ now: '2026-10-03T10:01:30Z', elapsed_seconds: 20 })
    const offset = clockOffset(running, browserNow)
    expect(offset).toBe(3_600_000)
    expect(liveSeconds(running, browserNow, offset)).toBe(110)
    expect(liveSeconds(running, browserNow + 5_000, offset)).toBe(115)
    expect(liveSeconds(running, browserNow, 0)).toBe(20)
  })

  it('is what the server counted while paused or stopped', () => {
    const paused = timer({ state: 'paused', running_since: null, elapsed_seconds: 300 })
    expect(liveSeconds(paused, Date.parse('2026-10-03T12:00:00Z'))).toBe(300)
    const stopped = timer({ state: 'stopped', running_since: null, elapsed_seconds: 301 })
    expect(liveSeconds(stopped, Date.parse('2026-10-03T12:00:00Z'))).toBe(301)
  })

  it('treats a body that is not a timer as none', () => {
    expect(asTimer(null)).toBeNull()
    expect(asTimer([])).toBeNull()
    expect(asTimer(timer({}))).not.toBeNull()
  })
})

describe('formatting', () => {
  it('writes m:ss, then h:mm:ss', () => {
    expect(formatClock(0)).toBe('0:00')
    expect(formatClock(462)).toBe('7:42')
    expect(formatClock(3729)).toBe('1:02:09')
  })

  it('shows a countdown’s time left, and its overtime with a plus', () => {
    const countdown = timer({ mode: 'countdown', target_seconds: 600 })
    expect(timerClock(countdown, 138)).toBe('7:42')
    expect(timerClock(countdown, 600)).toBe('0:00')
    expect(timerClock(countdown, 642)).toBe('+0:42')
    expect(timerClock(countdown, 600 + 3700)).toBe('+1:01:40')
    expect(timerClock(timer({}), 642)).toBe('10:42')
  })

  it('titles the tab by state', () => {
    const countdown = timer({ mode: 'countdown', target_seconds: 600 })
    expect(timerTitle(countdown, 138)).toBe('▶ 7:42 · art')
    expect(timerTitle({ ...countdown, state: 'paused' }, 138)).toBe('⏸ 7:42 · art')
    expect(timerTitle(countdown, 642)).toBe('+0:42 · art')
    expect(timerTitle({ ...countdown, state: 'stopped' }, 642)).toBe('待記錄 · art')
  })
})

describe('the start form', () => {
  it('defaults to 10 minutes Monday to Friday and 30 at the weekend', () => {
    // 2026-10-05 is a Monday.
    const days = [5, 6, 7, 8, 9, 10, 11].map((day) => defaultCountdownMinutes(new Date(2026, 9, day)))
    expect(days).toEqual([10, 10, 10, 10, 10, 30, 30])
  })

  it('sends a countdown’s target, a stopwatch none, and a drill or an exercise', () => {
    expect(startPayload({ mode: 'countdown', minutes: '30', exerciseId: '1', drillId: '5' })).toEqual({
      mode: 'countdown',
      target_seconds: 1800,
      drill_id: 5,
    })
    expect(startPayload({ mode: 'stopwatch', minutes: '30', exerciseId: '1', drillId: '' })).toEqual({
      mode: 'stopwatch',
      exercise_id: 1,
    })
    expect(startPayload({ mode: 'stopwatch' })).toEqual({ mode: 'stopwatch' })
  })

  it('accepts whole minutes of at least one', () => {
    expect(['1', '45'].map(validMinutes)).toEqual([true, true])
    expect(['', '0', '1.5', '-3'].map(validMinutes)).toEqual([false, false, false, false])
  })
})

describe('the record a stopped timer becomes', () => {
  it('rounds to the nearest minute, at least one', () => {
    expect(roundToMinutes(0)).toBe(1)
    expect(roundToMinutes(29)).toBe(1)
    expect(roundToMinutes(89)).toBe(1)
    expect(roundToMinutes(90)).toBe(2)
    expect(roundToMinutes(1250)).toBe(21)
  })

  it('fills its minutes, its drill and exercise, and the local date it started', () => {
    const started = new Date(2026, 9, 2, 23, 50)
    const form = timerRecordForm(
      timer({
        state: 'stopped',
        started_at: started.toISOString(),
        elapsed_seconds: 1250,
        activity: { exercise: { id: 1, display_name: '線條' }, drill: { id: 5, display_name: '基本線條' } },
      }),
    )
    expect(form).toMatchObject({
      date: '2026-10-02',
      duration_minutes: '21',
      exercise_id: '1',
      drill_id: '5',
      location_id: 'unchosen',
      tool_id: 'unchosen',
      kind: 'practice',
    })
  })

  it('asks for a check past three hours', () => {
    expect(isLongTimer(timer({ elapsed_seconds: 3 * 3600 }))).toBe(false)
    expect(isLongTimer(timer({ elapsed_seconds: 3 * 3600 + 1 }))).toBe(true)
  })
})

describe('the tone', () => {
  it('plays through Web Audio, and is skipped where there is none', () => {
    const started = vi.fn()
    class FakeAudioContext {
      currentTime = 0
      destination = {}
      createOscillator() {
        return { frequency: { setValueAtTime() {} }, connect() {}, start: started, stop() {} }
      }
      createGain() {
        return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }
      }
    }
    expect(playTone(FakeAudioContext)).toBe(true)
    expect(started).toHaveBeenCalledTimes(1)
    expect(playTone(null)).toBe(false)
  })
})
