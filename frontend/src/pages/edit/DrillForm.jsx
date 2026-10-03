// Frontend: add or edit a drill, /drills/new?exercise=:id and
// /drills/:id/edit.
//
// StageForm's shape: the parent is chosen from a select, and `?exercise=`
// preselects it - which is how an exercise's 新增練法 arrives. What it holds:
// the exercise (required), a name (blank falls back to the exercise's), the
// source through OptionPicker, the round (unit and target), suggested minutes,
// frequency, the instructions as Markdown, the source links and the resources
// as two lists of name + link rows, and a remark.
//
// Saving goes to the drill's own page, as saving an exercise goes to the
// exercise's. Cancel goes back where the form came from: the drill's page on
// an edit, the exercise it was opened from (else the drill library) on an add.
// Deleting goes to the exercise's page, the drill's being gone. Deleting a
// drill named by records is the server's 409, shown in the dialog.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import FormActions from '../../components/forms/FormActions'
import OptionPicker from '../../components/forms/OptionPicker'
import ResourceRows from '../../components/forms/ResourceRows'
import { Field, Input, Section, Select, TextArea } from '../../components/ui/primitives'
import { ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiMutation, useApiQuery, useOptions } from '../../hooks/useApi'
import { blankToNull, integerOrNull, resourcesFromApi, resourcesToPayload } from '../../lib/rowList'

// A drill shows in the drill library, on its own page, on its exercise's page
// (and the exercise's drill count), and a source's in_use count moves.
const INVALIDATE = [endpoints.drills.list(), endpoints.exercises.list(), endpoints.options.list()]

function emptyForm(exerciseId) {
  return {
    exercise_id: exerciseId ?? '',
    name: '',
    source_id: null,
    unit: '',
    target: '',
    suggested_minutes: '',
    frequency: '',
    instructions: '',
    source_links: [],
    resources: [],
    remark: '',
  }
}

function fromDrill(drill) {
  return {
    exercise_id: drill.exercise?.id == null ? '' : String(drill.exercise.id),
    name: drill.name ?? '',
    source_id: drill.source?.id ?? null,
    unit: drill.unit ?? '',
    target: drill.target == null ? '' : String(drill.target),
    suggested_minutes: drill.suggested_minutes == null ? '' : String(drill.suggested_minutes),
    frequency: drill.frequency ?? '',
    instructions: drill.instructions ?? '',
    source_links: resourcesFromApi(drill.source_links),
    resources: resourcesFromApi(drill.resources),
    remark: drill.remark ?? '',
  }
}

/** The form as the API's DrillWrite. The position is left to the server. */
function toPayload(form) {
  return {
    exercise_id: integerOrNull(form.exercise_id),
    name: blankToNull(form.name),
    source_id: form.source_id,
    unit: blankToNull(form.unit),
    target: integerOrNull(form.target),
    suggested_minutes: integerOrNull(form.suggested_minutes),
    frequency: blankToNull(form.frequency),
    instructions: blankToNull(form.instructions),
    source_links: resourcesToPayload(form.source_links),
    resources: resourcesToPayload(form.resources),
    remark: blankToNull(form.remark),
  }
}

export default function DrillForm() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const isNew = id === undefined
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const existing = useApiQuery(endpoints.drills.detail(id), null, { enabled: !isNew })
  const exercises = useApiQuery(endpoints.exercises.list())
  const sources = useOptions('source')
  const create = useApiMutation({ method: 'POST', invalidate: INVALIDATE })
  const update = useApiMutation({ method: 'PATCH', invalidate: INVALIDATE })

  const [form, setForm] = useState(() => emptyForm(searchParams.get('exercise')))
  const [loaded, setLoaded] = useState(null)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const saving = create.isPending || update.isPending

  // As NoteForm: adopt the loaded row during render, keyed on its id.
  if (!isNew && existing.data && loaded?.id !== existing.data.id) {
    setLoaded(existing.data)
    setForm(fromDrill(existing.data))
  }

  const set = (field) => (event) => setForm((previous) => ({ ...previous, [field]: event.target.value }))
  const setValue = (field) => (value) => setForm((previous) => ({ ...previous, [field]: value }))

  // Where Delete goes: the exercise the drill belonged to. Cancel goes there
  // too on an add, and back to the drill's page on an edit.
  const exerciseId = loaded?.exercise?.id ?? integerOrNull(form.exercise_id)
  const exercisePage = exerciseId ? `/exercises/${exerciseId}` : '/drills'
  const back = isNew ? exercisePage : `/drills/${id}`

  async function submit(event) {
    event.preventDefault()
    setError(null)
    const body = toPayload(form)
    if (body.exercise_id === null) {
      setError(new Error('要選一個練習項目。'))
      return
    }
    try {
      const saved = isNew
        ? await create.mutateAsync({ url: endpoints.drills.create(), body })
        : await update.mutateAsync({ url: endpoints.drills.update(id), body })
      navigate(`/drills/${saved.id}`)
    } catch (caught) {
      setError(caught)
    }
  }

  async function remove() {
    await fetchJson(endpoints.drills.remove(id), { method: 'DELETE' })
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate(exercisePage)
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-1">
        <h1 className="font-display text-2xl font-bold">{isNew ? '新增練法' : '編輯練法'}</h1>
        {!isNew && existing.data ? <p className="text-sm text-text-muted">{existing.data.display_name}</p> : null}
      </header>

      {!isNew && existing.isPending ? <Loading /> : null}
      {!isNew && existing.error ? <ErrorNote error={existing.error} /> : null}
      {exercises.error ? <ErrorNote error={exercises.error} /> : null}

      {isNew || existing.data ? (
        <>
          <Section title="練法">
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="練習項目">
                <Select value={form.exercise_id} onChange={set('exercise_id')}>
                  <option value="">選擇練習項目…</option>
                  {(exercises.data ?? []).map((exercise) => (
                    <option key={exercise.id} value={String(exercise.id)}>
                      {exercise.display_name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="名稱" hint="空白就用練習項目的名稱。">
                <Input value={form.name} onChange={set('name')} />
              </Field>
            </div>
          </Section>

          <Section title="來源">
            <OptionPicker label="來源" options={sources.data} value={form.source_id} onChange={setValue('source_id')} />
          </Section>

          <Section title="份量">
            <div className="grid gap-3 sm:grid-cols-4">
              <Field label="單位" hint="頁、張、組、個">
                <Input value={form.unit} onChange={set('unit')} />
              </Field>
              <Field label="目標" hint="一輪幾個單位。">
                <Input type="number" min="1" step="1" value={form.target} onChange={set('target')} />
              </Field>
              <Field label="建議分鐘">
                <Input
                  type="number"
                  min="1"
                  step="1"
                  value={form.suggested_minutes}
                  onChange={set('suggested_minutes')}
                />
              </Field>
              <Field label="頻率" hint="每天、daily for 3 weeks">
                <Input value={form.frequency} onChange={set('frequency')} />
              </Field>
            </div>
          </Section>

          <Section title="做法">
            <Field label="步驟" hint="Markdown。">
              <TextArea rows={8} value={form.instructions} onChange={set('instructions')} className="font-mono" />
            </Field>
          </Section>

          <Section title="來源連結">
            <ResourceRows rows={form.source_links} onChange={setValue('source_links')} noun="來源連結" />
          </Section>

          <Section title="資源">
            <ResourceRows rows={form.resources} onChange={setValue('resources')} />
          </Section>

          <Section title="其他">
            <Field label="備註">
              <TextArea rows={3} value={form.remark} onChange={set('remark')} />
            </Field>
          </Section>

          <FormActions
            saving={saving}
            error={error}
            ready={Boolean(exercises.data)}
            onCancel={() => navigate(back)}
            onDelete={isNew ? null : () => setDeleting(true)}
          />
        </>
      ) : null}

      {deleting ? (
        <DeleteDialog
          title={`刪除練法「${existing.data?.display_name ?? ''}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。它的來源連結和資源會一起刪掉；有紀錄的練法不能刪除。</p>
        </DeleteDialog>
      ) : null}
    </form>
  )
}
