// Frontend: the running timer, as every page reads it.
//
// The state lives in components/timer/TimerProvider.jsx, which the page frame
// (components/layout/Layout.jsx) puts around every route; this is the context
// and the hook that reads it, apart from the component so that file exports
// only a component.
import { createContext, useContext } from 'react'

export const TimerContext = createContext(null)

/**
 * { timer, seconds, isPending, error, start(body), pause(), resume(), stop(),
 * discard(), clear() } - `timer` is the TimerResponse or null, `seconds` its
 * live elapsed seconds. Each action resolves with the server's answer and
 * puts it in the cache; a 404 or 409 (another device moved the timer on)
 * refetches before it is rethrown.
 */
export function useTimer() {
  const value = useContext(TimerContext)
  if (!value) throw new Error('useTimer is used outside TimerProvider.')
  return value
}
