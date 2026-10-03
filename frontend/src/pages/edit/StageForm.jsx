// Frontend: add or edit a stage, /roadmap/stages/new?goal=:id and
// /roadmap/stages/:id/edit.
//
// NoteForm's shape. What it holds: the goal it belongs to (chosen from every
// goal; `?goal=` preselects one, which is how the roadmap's 新增階段 arrives),
// the three name slots (at least one), its position inside the goal (blank puts
// it last), the focus (description), the test piece, the status and the date
// it was passed, the resources as name + link rows (components/forms/
// ResourceRows), and a remark.
//
// The date follows GoalForm's rule: shown and sent only while the status is
// 已通過, filled with today when that is chosen and it is empty.
//
// Moving a stage to another goal lands it last there unless a position is
// sent, so the position is sent with a goal change only when it was edited
// too: the old goal's number means nothing in the new one.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import FormActions from '../../components/forms/FormActions'
import ResourceRows from '../../components/forms/ResourceRows'
import { Field, Input, Section, Select, TextArea } from '../../components/ui/primitives'
import { ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiMutation, useApiQuery } from '../../hooks/useApi'
import { DEFAULT_STAGE_STATUS, localToday, STAGE_DONE, STAGE_STATUSES } from '../../lib/roadmap'
import { blankToNull, integerOrNull, resourcesFromApi, resourcesToPayload } from '../../lib/rowList'

// A stage shows on the roadmap (every number after it may move) and its page.
const INVALIDATE = [endpoints.goals.list(), endpoints.stages.list()]

function emptyForm(goalId) {
  return {
    goal_id: goalId ?? '',
    name_cn: '',
    name_en: '',
    name_alt: '',
    position: '',
    description: '',
    test: '',
    status: DEFAULT_STAGE_STATUS,
    passed_on: '',
    remark: '',
    resources: [],
  }
}

function fromStage(stage) {
  return {
    goal_id: stage.goal?.id == null ? '' : String(stage.goal.id),
    name_cn: stage.name_cn ?? '',
    name_en: stage.name_en ?? '',
    name_alt: stage.name_alt ?? '',
    position: stage.position == null ? '' : String(stage.position),
    description: stage.description ?? '',
    test: stage.test ?? '',
    status: stage.status ?? DEFAULT_STAGE_STATUS,
    passed_on: stage.passed_on ?? '',
    remark: stage.remark ?? '',
    resources: resourcesFromApi(stage.resources),
  }
}

/**
 * The form as the API's StageWrite. `loaded` is the stage being edited, or
 * null for a new one: it decides whether the position still applies.
 */
function toPayload(form, loaded) {
  const body = {
    goal_id: integerOrNull(form.goal_id),
    name_cn: blankToNull(form.name_cn),
    name_en: blankToNull(form.name_en),
    name_alt: blankToNull(form.name_alt),
    description: blankToNull(form.description),
    test: blankToNull(form.test),
    status: form.status,
    remark: blankToNull(form.remark),
    resources: resourcesToPayload(form.resources),
  }
  const position = integerOrNull(form.position)
  const goalMoved = loaded && loaded.goal?.id !== body.goal_id
  if (position !== null && (!goalMoved || position !== loaded.position)) body.position = position
  if (form.status === STAGE_DONE) body.passed_on = blankToNull(form.passed_on)
  return body
}

export default function StageForm() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const isNew = id === undefined
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const existing = useApiQuery(endpoints.stages.detail(id), null, { enabled: !isNew })
  const goals = useApiQuery(endpoints.goals.list())
  const create = useApiMutation({ method: 'POST', invalidate: INVALIDATE })
  const update = useApiMutation({ method: 'PATCH', invalidate: INVALIDATE })

  const [form, setForm] = useState(() => emptyForm(searchParams.get('goal')))
  const [loaded, setLoaded] = useState(null)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const saving = create.isPending || update.isPending

  // As NoteForm: adopt the loaded row during render, keyed on its id.
  if (!isNew && existing.data && loaded?.id !== existing.data.id) {
    setLoaded(existing.data)
    setForm(fromStage(existing.data))
  }

  const set = (field) => (event) => setForm((previous) => ({ ...previous, [field]: event.target.value }))
  const setValue = (field) => (value) => setForm((previous) => ({ ...previous, [field]: value }))

  function setStatus(event) {
    const status = event.target.value
    setForm((previous) => ({
      ...previous,
      status,
      passed_on: status === STAGE_DONE && !previous.passed_on ? localToday() : previous.passed_on,
    }))
  }

  async function submit(event) {
    event.preventDefault()
    setError(null)
    const body = toPayload(form, isNew ? null : loaded)
    if (body.goal_id === null) {
      setError(new Error('要選一個等級。'))
      return
    }
    if (!body.name_cn && !body.name_en && !body.name_alt) {
      setError(new Error('至少要有一個名稱。'))
      return
    }
    try {
      const saved = isNew
        ? await create.mutateAsync({ url: endpoints.stages.create(), body })
        : await update.mutateAsync({ url: endpoints.stages.update(id), body })
      navigate(`/roadmap/stages/${saved.id}`)
    } catch (caught) {
      setError(caught)
    }
  }

  async function remove() {
    await fetchJson(endpoints.stages.remove(id), { method: 'DELETE' })
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/roadmap')
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-1">
        <h1 className="font-display text-2xl font-bold">{isNew ? '新增階段' : '編輯階段'}</h1>
        {!isNew && existing.data ? (
          <p className="text-sm text-text-muted">
            階段 {existing.data.number} · {existing.data.display_name}
          </p>
        ) : null}
      </header>

      {!isNew && existing.isPending ? <Loading /> : null}
      {!isNew && existing.error ? <ErrorNote error={existing.error} /> : null}
      {goals.error ? <ErrorNote error={goals.error} /> : null}

      {isNew || existing.data ? (
        <>
          <Section title="名稱">
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="中文名">
                <Input value={form.name_cn} onChange={set('name_cn')} />
              </Field>
              <Field label="英文名">
                <Input value={form.name_en} onChange={set('name_en')} />
              </Field>
              <Field label="其他名稱">
                <Input value={form.name_alt} onChange={set('name_alt')} />
              </Field>
            </div>
          </Section>

          <Section title="位置">
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="等級" className="sm:col-span-2">
                <Select value={form.goal_id} onChange={set('goal_id')}>
                  <option value="">選擇等級…</option>
                  {(goals.data ?? []).map((goal) => (
                    <option key={goal.id} value={String(goal.id)}>
                      {goal.code} {goal.display_name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="順序" hint="在等級裡的位置；空白就排在最後。">
                <Input type="number" step="1" value={form.position} onChange={set('position')} />
              </Field>
            </div>
          </Section>

          <Section title="內容">
            <div className="space-y-3">
              <Field label="重點" hint="這個階段練什麼。">
                <TextArea rows={3} value={form.description} onChange={set('description')} />
              </Field>
              <Field label="測驗" hint="用來檢驗這個階段的作品。">
                <TextArea rows={2} value={form.test} onChange={set('test')} />
              </Field>
            </div>
          </Section>

          <Section title="進度">
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="狀態">
                <Select value={form.status} onChange={setStatus}>
                  {STAGE_STATUSES.map((entry) => (
                    <option key={entry.value} value={entry.value}>
                      {entry.label}
                    </option>
                  ))}
                </Select>
              </Field>
              {form.status === STAGE_DONE ? (
                <Field label="通過日期">
                  <Input type="date" value={form.passed_on} onChange={set('passed_on')} />
                </Field>
              ) : null}
            </div>
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
            ready={Boolean(goals.data)}
            onCancel={() => navigate(isNew ? '/roadmap' : `/roadmap/stages/${id}`)}
            onDelete={isNew ? null : () => setDeleting(true)}
          />
        </>
      ) : null}

      {deleting ? (
        <DeleteDialog
          title={`刪除階段「${existing.data?.display_name ?? ''}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。它的資源會一起刪掉；之後的階段編號會往前移。</p>
        </DeleteDialog>
      ) : null}
    </form>
  )
}
