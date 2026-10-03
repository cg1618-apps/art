// Frontend: the timer, /timer.
//
// With no timer, the start form: countdown or stopwatch; for a countdown the
// 10 and 30 minute presets and a number of minutes, defaulting by the day of
// the week (lib/timer.js); and optionally an exercise, then one of its drills.
// `?drill=` preselects a drill and its exercise, `?exercise=` an exercise -
// as the record form's.
//
// With a timer: what it times, the clock in large digits, and pause / resume,
// 停止 and 捨棄. 停止 freezes it on the server and opens the record form
// prefilled from it (/records/new?from=timer); 捨棄 throws the session away,
// after a confirm. A stopped timer that was not recorded yet waits here, with
// 記錄 back to that form.
//
// The timer's state is TimerProvider's (components/timer/), shared with the
// chip in the top bar; this page only draws it and calls its actions.
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { endpoints } from '../../api/endpoints'
import ActivitySelect from '../../components/forms/ActivitySelect'
import Dialog from '../../components/ui/Dialog'
import { Button, Card, Field, Input, LinkButton } from '../../components/ui/primitives'
import { ErrorNote, Loading } from '../../components/ui/states'
import { useApiQuery } from '../../hooks/useApi'
import { useTimer } from '../../hooks/useTimer'
import { cx } from '../../lib/cx'
import {
  COUNTDOWN,
  COUNTDOWN_PRESETS,
  defaultCountdownMinutes,
  isCountdown,
  isOvertime,
  isPaused,
  isRunning,
  isStopped,
  startPayload,
  timerClock,
  timerDrill,
  timerExercise,
  TIMER_MODES,
  validMinutes,
} from '../../lib/timer'

const RECORD_FORM = '/records/new?from=timer'

function Toggle({ pressed, onClick, children, ...rest }) {
  return (
    <Button kind={pressed ? 'primary' : 'outline'} aria-pressed={pressed} onClick={onClick} {...rest}>
      {children}
    </Button>
  )
}

function StartForm() {
  const { start } = useTimer()
  const [searchParams] = useSearchParams()
  const drillParam = searchParams.get('drill')
  const [mode, setMode] = useState(COUNTDOWN)
  const [minutes, setMinutes] = useState(() => String(defaultCountdownMinutes()))
  const [activity, setActivity] = useState(() => ({
    exerciseId: drillParam ? '' : (searchParams.get('exercise') ?? ''),
    drillId: drillParam ?? '',
  }))
  const [error, setError] = useState(null)
  const [starting, setStarting] = useState(false)

  const exercises = useApiQuery(endpoints.exercises.list())
  const arrivingDrill = useApiQuery(endpoints.drills.detail(drillParam), null, { enabled: Boolean(drillParam) })

  // A drill arriving by ?drill= brings its exercise, once.
  const drillExerciseId = arrivingDrill.data?.exercise?.id
  if (drillExerciseId != null && activity.drillId === drillParam && activity.exerciseId === '') {
    setActivity((previous) => ({ ...previous, exerciseId: String(drillExerciseId) }))
  }

  const exercise = useApiQuery(endpoints.exercises.detail(activity.exerciseId), null, {
    enabled: activity.exerciseId !== '',
  })

  const countdown = mode === COUNTDOWN
  const ready = !drillParam || activity.exerciseId !== ''

  async function submit(event) {
    event.preventDefault()
    setError(null)
    if (countdown && !validMinutes(minutes)) {
      setError(new Error('分鐘要是 1 以上的整數。'))
      return
    }
    setStarting(true)
    try {
      await start(startPayload({ mode, minutes, ...activity }))
    } catch (caught) {
      // A 409 means one was started elsewhere; the page now shows it.
      if (caught.status !== 409) setError(caught)
      setStarting(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-6">
      <div role="group" aria-label="模式" className="flex gap-2">
        {TIMER_MODES.map((entry) => (
          <Toggle key={entry.value} pressed={mode === entry.value} onClick={() => setMode(entry.value)}>
            {entry.label}
          </Toggle>
        ))}
      </div>

      {countdown ? (
        <div className="flex flex-wrap items-end gap-3">
          <div role="group" aria-label="預設" className="flex gap-2">
            {COUNTDOWN_PRESETS.map((preset) => (
              <Toggle
                key={preset}
                pressed={minutes === String(preset)}
                onClick={() => setMinutes(String(preset))}
              >
                {preset} 分鐘
              </Toggle>
            ))}
          </div>
          <Field label="分鐘" className="w-28">
            <Input
              type="number"
              min="1"
              step="1"
              required
              value={minutes}
              onChange={(event) => setMinutes(event.target.value)}
            />
          </Field>
        </div>
      ) : (
        <p className="text-sm text-text-muted">碼錶從 0 開始往上數。</p>
      )}

      {exercises.error ? <ErrorNote error={exercises.error} /> : null}
      {arrivingDrill.error ? <ErrorNote error={arrivingDrill.error} /> : null}
      <ActivitySelect
        exercises={exercises.data}
        drills={exercise.data?.drills}
        exerciseId={activity.exerciseId}
        drillId={activity.drillId}
        onChange={setActivity}
        drillHint="可以不指定。"
      />

      <div className="space-y-3 border-t border-border pt-4">
        {error ? <ErrorNote error={error} /> : null}
        <Button type="submit" kind="primary" disabled={starting || !ready}>
          {starting ? '開始中…' : '開始'}
        </Button>
      </div>
    </form>
  )
}

function Activity({ timer }) {
  const exercise = timerExercise(timer)
  const drill = timerDrill(timer)
  if (!exercise) return <p className="text-text-muted">不指定練習</p>
  return (
    <p className="text-text-muted">
      <Link to={`/exercises/${exercise.id}`} className="hover:text-brand hover:underline">
        {exercise.display_name}
      </Link>
      {drill && drill.display_name !== exercise.display_name ? ` · ${drill.display_name}` : null}
    </p>
  )
}

function DiscardDialog({ onClose }) {
  const { discard } = useTimer()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function confirm() {
    setBusy(true)
    setError(null)
    try {
      await discard()
    } catch (caught) {
      setError(caught)
      setBusy(false)
    }
  }

  return (
    <Dialog
      title="捨棄這次計時？"
      onClose={onClose}
      busy={busy}
      footer={
        <>
          <Button onClick={onClose} disabled={busy}>
            保留
          </Button>
          <Button kind="danger" onClick={confirm} disabled={busy}>
            {busy ? '捨棄中…' : '捨棄'}
          </Button>
        </>
      }
    >
      <div className="space-y-3 text-text">
        <p>這段時間不會留下紀錄。</p>
        {error ? <ErrorNote error={error} /> : null}
      </div>
    </Dialog>
  )
}

function RunningTimer({ timer, seconds }) {
  const { pause, resume, stop } = useTimer()
  const navigate = useNavigate()
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [discarding, setDiscarding] = useState(false)
  const stopped = isStopped(timer)
  const overtime = isOvertime(timer, seconds)

  async function run(action, after) {
    setError(null)
    setBusy(true)
    try {
      await action()
      after?.()
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  let status
  if (stopped) status = '已停止，待記錄'
  else if (isPaused(timer)) status = '暫停中'
  else if (overtime) status = '超時'
  else status = isCountdown(timer) ? '倒數中' : '計時中'

  return (
    <Card className="space-y-6 py-8 text-center">
      <div className="space-y-1">
        <Activity timer={timer} />
        <p className={cx('text-sm', overtime || stopped ? 'text-warn' : 'text-text-faint')}>
          {status}
          {isCountdown(timer) ? ` · 倒數 ${Math.round(timer.target_seconds / 60)} 分鐘` : ' · 碼錶'}
        </p>
      </div>
      <p
        role="timer"
        aria-label="計時"
        className={cx(
          'font-display text-7xl font-bold tabular-nums sm:text-8xl',
          overtime ? 'text-warn' : 'text-text',
          (isPaused(timer) || stopped) && 'opacity-60',
        )}
      >
        {timerClock(timer, seconds)}
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {stopped ? (
          <LinkButton to={RECORD_FORM} kind="primary">
            記錄
          </LinkButton>
        ) : (
          <>
            {isRunning(timer) ? (
              <Button kind="primary" onClick={() => run(pause)} disabled={busy}>
                暫停
              </Button>
            ) : (
              <Button kind="primary" onClick={() => run(resume)} disabled={busy}>
                繼續
              </Button>
            )}
            <Button onClick={() => run(stop, () => navigate(RECORD_FORM))} disabled={busy}>
              停止
            </Button>
          </>
        )}
        <Button kind="danger" onClick={() => setDiscarding(true)} disabled={busy}>
          捨棄
        </Button>
      </div>
      {error ? <ErrorNote error={error} /> : null}
      {discarding ? <DiscardDialog onClose={() => setDiscarding(false)} /> : null}
    </Card>
  )
}

export default function Timer() {
  const { timer, seconds, isPending, error } = useTimer()
  let body
  if (isPending) body = <Loading />
  else if (error && !timer) body = <ErrorNote error={error} />
  else if (timer) body = <RunningTimer timer={timer} seconds={seconds} />
  else body = <StartForm />

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="font-display text-2xl font-bold">計時</h1>
      {body}
    </div>
  )
}
