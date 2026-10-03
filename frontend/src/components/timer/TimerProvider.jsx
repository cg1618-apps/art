// Frontend: the running timer's state, around every page.
//
// The server holds the timer; this reads GET /api/timer - on mount, when the
// window regains focus, and every 30 s, so a timer started or stopped on the
// phone shows here - and ticks once a second, locally, only while it runs.
// The live figure is lib/timer.js's, against the server's clock: the offset is
// the response's `now` against the moment TanStack received it.
//
// Two side effects belong to the timer rather than to any page, so they are
// here:
//   - the tab title, "▶ 7:42 · art", while a timer exists;
//   - one tone when a countdown reaches zero. Once per timer, and not when a
//     page opens on a countdown already past zero - that is not a crossing.
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useRef, useState } from 'react'

import { fetchJson, jsonBody } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import { useApiQuery } from '../../hooks/useApi'
import { TimerContext } from '../../hooks/useTimer'
import {
  asTimer,
  clockOffset,
  isRunning,
  liveSeconds,
  playTone,
  remainingSeconds,
  timerTitle,
} from '../../lib/timer'

export const TIMER_REFETCH_MS = 30_000
const TICK_MS = 1000

const atZero = (timer, seconds) => {
  const remaining = remainingSeconds(timer, seconds)
  return remaining !== null && remaining <= 0
}

// Whether the timer is at zero at this moment, rather than at the last tick.
const atZeroNow = (timer, offset) => atZero(timer, liveSeconds(timer, Date.now(), offset))

export default function TimerProvider({ children }) {
  const queryClient = useQueryClient()
  const url = endpoints.timer.current()
  const query = useApiQuery(url, null, {
    staleTime: 0,
    refetchInterval: TIMER_REFETCH_MS,
    refetchOnWindowFocus: true,
  })
  const timer = asTimer(query.data)
  const offset = clockOffset(timer, query.dataUpdatedAt)
  const running = isRunning(timer)
  const runningSince = timer?.running_since ?? null

  const [clientNow, setClientNow] = useState(() => Date.now())
  useEffect(() => {
    if (!running) return undefined
    const tick = () => setClientNow(Date.now())
    tick()
    const interval = setInterval(tick, TICK_MS)
    return () => clearInterval(interval)
  }, [running, runningSince])

  const seconds = liveSeconds(timer, clientNow, offset)

  // The tone. The first sight of a timer only notes whether it is already at
  // zero, measured now rather than at the last tick.
  const crossed = atZero(timer, seconds)
  const toneFor = useRef(null)
  const timerId = timer?.id ?? null
  useEffect(() => {
    if (timerId === null) {
      toneFor.current = null
      return
    }
    if (toneFor.current?.id !== timerId) {
      toneFor.current = { id: timerId, done: atZeroNow(timer, offset) }
      return
    }
    if (crossed && !toneFor.current.done) {
      toneFor.current.done = true
      playTone()
    }
  }, [timerId, crossed, timer, offset])

  const title = timer ? timerTitle(timer, seconds) : null
  useEffect(() => {
    if (!title) return undefined
    const previous = document.title
    document.title = title
    return () => {
      document.title = previous
    }
  }, [title])

  const actions = useMemo(() => {
    const key = [url, null]
    const put = (body) => queryClient.setQueryData(key, body)

    async function send(target, options) {
      try {
        return await fetchJson(target, options)
      } catch (caught) {
        // Another device moved the timer on: show what the server holds.
        if (caught.status === 404 || caught.status === 409) {
          await queryClient.invalidateQueries({ queryKey: key })
        }
        throw caught
      }
    }

    const post = (target, body) => send(target, { method: 'POST', ...(body ? jsonBody(body) : {}) })

    return {
      async start(body) {
        const created = await post(endpoints.timer.create(), body)
        put(created)
        return created
      },
      async pause() {
        const paused = await post(endpoints.timer.pause())
        put(paused)
        return paused
      },
      async resume() {
        const resumed = await post(endpoints.timer.resume())
        put(resumed)
        return resumed
      },
      async stop() {
        const stopped = await post(endpoints.timer.stop())
        put(stopped)
        return stopped
      },
      /** PATCH /api/timer - the activity and the record draft. */
      async update(body) {
        const updated = await send(endpoints.timer.update(), { method: 'PATCH', ...jsonBody(body) })
        put(updated)
        return updated
      },
      /**
       * The draft as the page holds it, put in the cache before it is saved,
       * so a page opened before the save lands - the record form, /timer -
       * starts from it rather than from the last saved one.
       */
      holdDraft(draft) {
        queryClient.setQueryData(key, (current) => (asTimer(current) ? { ...current, draft } : current))
      },
      async discard() {
        await send(endpoints.timer.remove(), { method: 'DELETE' })
        put(null)
      },
      /** The timer is gone - recorded through POST /api/timer/record. */
      clear() {
        put(null)
      },
    }
  }, [queryClient, url])

  const value = {
    timer,
    seconds,
    isPending: query.isPending,
    error: query.error,
    ...actions,
  }

  return <TimerContext.Provider value={value}>{children}</TimerContext.Provider>
}
