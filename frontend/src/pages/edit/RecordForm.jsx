// Frontend: add or edit a record, /records/new and /records/:id/edit.
//
// NoteForm's shape. What it holds, in the order a session is logged:
//
//   - the date, today in the browser's time zone for a new record;
//   - the location, a new record's defaulting to the newest record's;
//   - what was practised: one exercise, then optionally one of its drills.
//     `?drill=` preselects a drill (and its exercise), `?exercise=` an
//     exercise - how a drill's 記錄 and an exercise's page arrive. A record
//     names a drill or an exercise, never both: with a drill the exercise is
//     sent as null and the server derives it;
//   - the kind, 練習 / 作品 / 測驗. A test names exactly one stage or one level,
//     chosen in one select (components/forms/RoadmapSelect), so both is not a
//     choice the form can make; any other kind sends neither;
//   - the method, whose description shows where it is picked;
//   - the tool, a new record's defaulting to Clip Studio Paint;
//   - the minutes, the reference links as name + link rows, and notes.
//
// The two defaults are applied when the page has loaded them, not by an
// effect: an untouched field is UNCHOSEN and resolved at render and on save
// (lib/records.js), so a click - including one that clears it - wins. Save
// waits until the defaults are known.
//
// Saving and deleting return to /records.
//
// `/records/new?from=timer` is the same form for a stopped timer
// (components/timer/): it opens with the timer's minutes (to the nearest
// minute, at least 1), its drill or exercise and the local date it started,
// plus the usual defaults, and its save posts to /api/timer/record, which
// creates the record and ends the timer together. A timer that ran over 3
// hours says so beside the minutes. Leaving keeps the timer stopped and owed a
// record - the top bar says 待記錄 - and 取消 goes back to /timer.
//
// The timer's record draft opens with it (lib/timer.js's timerRecordForm), and
// this form's edits are saved back to the timer as they are typed
// (hooks/useDraftAutosave): leaving and coming back - or opening /timer -
// finds them. Saving sends the draft first, then the record - whose body is
// the record; the draft is not merged into it on the server.
//
// The fields other than the date and minutes are components/forms/
// RecordFields, shared with the timer page's draft.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import FormActions from '../../components/forms/FormActions'
import RecordFields from '../../components/forms/RecordFields'
import { Field, Input, LinkButton } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiMutation, useApiQuery } from '../../hooks/useApi'
import { useDraftAutosave } from '../../hooks/useDraftAutosave'
import { useRecordDefaults } from '../../hooks/useRecordDefaults'
import { useTimer } from '../../hooks/useTimer'
import { emptyRecordForm, fromRecord, recordToPayload, TEST_KIND } from '../../lib/records'
import { formatClock, isLongTimer, isStopped, timerRecordForm } from '../../lib/timer'

// A record shows in the log, on its exercise's page (and the exercise's
// counts, and its drill's in the drill library), on its stage's page when it
// is a test, and in options' in_use.
const INVALIDATE = [
  endpoints.records.list(),
  endpoints.exercises.list(),
  endpoints.drills.list(),
  endpoints.options.list(),
]

export default function RecordForm() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const isNew = id === undefined
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const fromTimer = isNew && searchParams.get('from') === 'timer'
  const drillParam = isNew && !fromTimer ? searchParams.get('drill') : null
  const timers = useTimer()
  // The stopped timer this form records, or null.
  const pending = fromTimer && isStopped(timers.timer) ? timers.timer : null

  const existing = useApiQuery(endpoints.records.detail(id), null, { enabled: !isNew })
  const recordDefaults = useRecordDefaults({ enabled: isNew })
  const arrivingDrill = useApiQuery(endpoints.drills.detail(drillParam), null, { enabled: Boolean(drillParam) })
  const exercises = useApiQuery(endpoints.exercises.list())
  const goals = useApiQuery(endpoints.goals.list())
  const create = useApiMutation({ method: 'POST', invalidate: INVALIDATE })
  const update = useApiMutation({ method: 'PATCH', invalidate: INVALIDATE })

  const [form, setForm] = useState(() =>
    emptyRecordForm({ drill: drillParam, exercise: isNew && !fromTimer ? searchParams.get('exercise') : null }),
  )
  const [loaded, setLoaded] = useState(null)
  const [adoptedTimer, setAdoptedTimer] = useState(null)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const saving = create.isPending || update.isPending

  // As NoteForm: adopt the loaded row during render, keyed on its id.
  if (!isNew && existing.data && loaded?.id !== existing.data.id) {
    setLoaded(existing.data)
    setForm(fromRecord(existing.data))
  }

  // And a stopped timer, once, keyed on its id - with its record draft.
  if (pending && adoptedTimer !== pending.id) {
    setAdoptedTimer(pending.id)
    setForm(timerRecordForm(pending))
  }

  // A timer's form keeps its edits on the timer until it is saved.
  const draftSaver = useDraftAutosave(pending && adoptedTimer === pending.id ? pending.id : null, form)

  // A drill arriving by ?drill= brings its exercise, once.
  const drillExerciseId = arrivingDrill.data?.exercise?.id
  if (drillExerciseId != null && form.drill_id === drillParam && form.exercise_id === '') {
    setForm((previous) => ({ ...previous, exercise_id: String(drillExerciseId) }))
  }

  const defaults = recordDefaults.defaults

  const set = (field) => (event) => setForm((previous) => ({ ...previous, [field]: event.target.value }))

  const ready =
    Boolean(exercises.data && goals.data) &&
    (!isNew || (!recordDefaults.isPending && (!drillParam || form.exercise_id !== ''))) &&
    (!fromTimer || adoptedTimer !== null)

  async function leave() {
    if (!fromTimer) {
      navigate('/records')
      return
    }
    // What was typed lands before /timer reads the timer.
    await draftSaver.flush()
    navigate('/timer')
  }

  async function submit(event) {
    event.preventDefault()
    setError(null)
    const body = recordToPayload(form, defaults)
    if (!body.date) {
      setError(new Error('要有日期。'))
      return
    }
    if (body.kind === TEST_KIND && body.stage_id === null && body.goal_id === null) {
      setError(new Error('測驗要選一個階段或一個等級。'))
      return
    }
    try {
      if (fromTimer) {
        // The draft is saved first, so a refused record loses nothing typed;
        // the record itself is this body, not the draft.
        await draftSaver.flush()
        await create.mutateAsync({ url: endpoints.timer.record(), body })
        navigate('/records')
        timers.clear()
        return
      }
      if (isNew) await create.mutateAsync({ url: endpoints.records.create(), body })
      else await update.mutateAsync({ url: endpoints.records.update(id), body })
      navigate('/records')
    } catch (caught) {
      setError(caught)
    }
  }

  async function remove() {
    await fetchJson(endpoints.records.remove(id), { method: 'DELETE' })
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/records')
  }

  if (fromTimer && !pending) {
    if (timers.isPending) return <Loading />
    return (
      <Empty action={<LinkButton to="/timer">到計時</LinkButton>}>
        {timers.timer ? '計時還沒停止。' : '沒有待記錄的計時。'}
      </Empty>
    )
  }

  const durationHint =
    pending && isLongTimer(pending) ? (
      <span className="font-medium text-warn">
        計時了 {formatClock(pending.elapsed_seconds)}，超過 3 小時：請確認分鐘數。
      </span>
    ) : (
      '可以不填。'
    )

  return (
    <form onSubmit={submit} className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-1">
        <h1 className="font-display text-2xl font-bold">{isNew ? '新增紀錄' : '編輯紀錄'}</h1>
        {pending ? (
          <p className="text-sm text-text-muted">來自計時 · {formatClock(pending.elapsed_seconds)}</p>
        ) : null}
        {!isNew && existing.data ? <p className="text-sm text-text-muted">{existing.data.date}</p> : null}
      </header>

      {!isNew && existing.isPending ? <Loading /> : null}
      {!isNew && existing.error ? <ErrorNote error={existing.error} /> : null}
      {exercises.error ? <ErrorNote error={exercises.error} /> : null}
      {arrivingDrill.error ? <ErrorNote error={arrivingDrill.error} /> : null}

      {isNew || existing.data ? (
        <>
          <RecordFields
            form={form}
            setForm={setForm}
            defaults={defaults}
            when={
              <div className="grid gap-3 sm:grid-cols-3">
                <Field label="日期">
                  <Input type="date" required value={form.date} onChange={set('date')} />
                </Field>
                <Field label="分鐘" hint={durationHint}>
                  <Input
                    type="number"
                    min="0"
                    step="1"
                    value={form.duration_minutes}
                    onChange={set('duration_minutes')}
                  />
                </Field>
              </div>
            }
          />

          <FormActions
            saving={saving}
            error={error}
            ready={ready}
            onCancel={leave}
            onDelete={isNew ? null : () => setDeleting(true)}
          />
        </>
      ) : null}

      {deleting ? (
        <DeleteDialog
          title={`刪除 ${existing.data?.date ?? ''} 的紀錄？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。它的參考連結會一起刪掉。</p>
        </DeleteDialog>
      ) : null}
    </form>
  )
}
