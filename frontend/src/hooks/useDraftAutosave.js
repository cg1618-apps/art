// Frontend: saving the timer's record draft as it is typed.
//
// The timer page and the record form opened from a timer both hold a record
// form whose activity and draft belong to the timer on the server
// (PATCH /api/timer, lib/timer.js's draftPayload). This saves that form a
// moment after the typing stops, so a refresh, another device or a page left
// and come back to finds what was typed.
//
//   - The first form seen for a timer is the one adopted from the server, and
//     is not saved back. Each later change is, DRAFT_SAVE_DELAY_MS after the
//     last one; a change undone before then sends nothing.
//   - The draft is put in the query cache at once (TimerProvider's holdDraft),
//     so a page that opens before the save lands starts from it.
//   - Saves go one at a time, in order: a slow one is never overtaken by the
//     next and then written over it.
//   - flush() sends a waiting change now and resolves when every save has
//     settled - the page calls it before 停止, 記錄 and anything else that
//     moves the timer or leaves. cancel() drops a waiting change (捨棄, and the
//     record form's save, whose body is the record). Neither rejects: a failed
//     save is the status's error, and the next change tries again.
//   - Leaving the page flushes, without waiting.
//
// status is { phase: 'idle' | 'saving' | 'saved' | 'error', error }.
import { useCallback, useEffect, useRef, useState } from 'react'

import { draftPayload } from '../lib/timer'
import { useTimer } from './useTimer'

export const DRAFT_SAVE_DELAY_MS = 800

const IDLE = { phase: 'idle', error: null }

/** `timerId` null turns it off; `form` is the record form's state. */
export function useDraftAutosave(timerId, form, { delay = DRAFT_SAVE_DELAY_MS } = {}) {
  const { update, holdDraft } = useTimer()
  const key = timerId == null ? null : JSON.stringify(draftPayload(form))

  // { id: the timer the baseline is for, sent: the key last sent (or adopted),
  //   waiting: { key, timeout } or null, inFlight: the last save, settled or not,
  //   saves: how many are unsettled }
  const saver = useRef({ id: null, sent: null, waiting: null, inFlight: Promise.resolve(), saves: 0 })
  const actions = useRef({ update, holdDraft })
  useEffect(() => {
    actions.current = { update, holdDraft }
  })
  const [status, setStatus] = useState(IDLE)

  const send = useCallback((sentKey) => {
    const s = saver.current
    s.sent = sentKey
    s.saves += 1
    setStatus({ phase: 'saving', error: null })
    s.inFlight = s.inFlight
      .then(() => actions.current.update(JSON.parse(sentKey)))
      .then(
        () => {
          s.saves -= 1
          if (s.saves === 0 && !s.waiting) setStatus({ phase: 'saved', error: null })
        },
        (error) => {
          s.saves -= 1
          // Not saved: the same form typed again is sent again.
          if (s.sent === sentKey) s.sent = null
          setStatus({ phase: 'error', error })
        },
      )
    return s.inFlight
  }, [])

  const cancel = useCallback(() => {
    const s = saver.current
    if (s.waiting) clearTimeout(s.waiting.timeout)
    s.waiting = null
    return s.inFlight
  }, [])

  const flush = useCallback(() => {
    const s = saver.current
    if (!s.waiting) return s.inFlight
    const { key: waitingKey } = s.waiting
    cancel()
    return send(waitingKey)
  }, [cancel, send])

  useEffect(() => {
    const s = saver.current
    if (key === null) {
      cancel()
      s.id = null
      return
    }
    if (s.id !== timerId) {
      // The form adopted from the server: what it holds is already saved.
      cancel()
      s.id = timerId
      s.sent = key
      return
    }
    if (key === s.sent) {
      // Typed back to what was last sent.
      if (s.waiting) {
        cancel()
        if (s.saves === 0) setStatus({ phase: 'saved', error: null })
      }
      return
    }
    cancel()
    actions.current.holdDraft(JSON.parse(key).draft)
    const waiting = {
      key,
      timeout: setTimeout(() => {
        if (s.waiting !== waiting) return
        s.waiting = null
        send(key)
      }, delay),
    }
    s.waiting = waiting
    setStatus({ phase: 'saving', error: null })
  }, [key, timerId, delay, cancel, send])

  // Leaving sends what is waiting.
  useEffect(() => () => void flush(), [flush])

  return { status, flush, cancel }
}
