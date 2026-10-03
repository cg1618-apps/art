// Frontend: the timer in the top bar, on every page while one exists.
//
// What it times and the clock - the time left on a countdown, "+0:42" in
// overtime (coloured), the elapsed time on a stopwatch - linking to /timer,
// with pause / resume beside it. A stopped timer is owed a record, so the chip
// says 待記錄 and leads back to the record form.
import { Link } from 'react-router-dom'

import { useTimer } from '../../hooks/useTimer'
import { cx } from '../../lib/cx'
import { isOvertime, isPaused, isRunning, isStopped, timerActivityName, timerClock } from '../../lib/timer'
import { FOCUS_RING } from '../ui/primitives'

const SHELL = 'inline-flex items-center gap-1 rounded-full border text-sm leading-tight'

export default function TimerChip() {
  const { timer, seconds, pause, resume } = useTimer()
  if (!timer) return null
  const name = timerActivityName(timer)

  if (isStopped(timer)) {
    return (
      <Link
        to="/records/new?from=timer"
        className={cx(SHELL, FOCUS_RING, 'border-warn/40 bg-warn-soft px-3 py-1 text-warn hover:border-warn')}
      >
        <span className="font-medium">待記錄</span>
        {name ? <span className="max-w-[10rem] truncate">· {name}</span> : null}
      </Link>
    )
  }

  const overtime = isOvertime(timer, seconds)
  const paused = isPaused(timer)
  return (
    <span
      className={cx(
        SHELL,
        'bg-surface pr-1',
        overtime ? 'border-warn/60 text-warn' : 'border-border-strong text-text',
      )}
    >
      <Link to="/timer" className={cx('inline-flex items-center gap-1.5 rounded-full py-1 pl-3', FOCUS_RING)}>
        {name ? <span className="max-w-[10rem] truncate text-text-muted">{name}</span> : null}
        <span className={cx('font-medium tabular-nums', paused && 'opacity-60')}>{timerClock(timer, seconds)}</span>
      </Link>
      <button
        type="button"
        onClick={() => (isRunning(timer) ? pause() : resume()).catch(() => {})}
        aria-label={paused ? '繼續計時' : '暫停計時'}
        className={cx('rounded-full px-1.5 py-0.5 text-xs text-text-muted hover:bg-surface-2 hover:text-text', FOCUS_RING)}
      >
        {paused ? '▶' : '⏸'}
      </button>
    </span>
  )
}
