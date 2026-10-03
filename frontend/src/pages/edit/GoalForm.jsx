// Frontend: add or edit a goal - a level - /roadmap/goals/new and
// /roadmap/goals/:id/edit.
//
// NoteForm's shape: titled sections, the error above Save, Cancel back to the
// roadmap, Delete through the shared dialog. A goal has no page of its own -
// the roadmap is where it is read - so saving and deleting both return there.
//
// What it holds: the code (`L0` …, required, unique), the three name slots (at
// least one, `ck_goal_has_a_name`), its position on the roadmap (blank puts a
// new goal last), what "done" means, the test piece, the status, the date it
// was achieved and a remark.
//
// The date is shown only while the status is 已達成: the server refuses a date
// with any other status and clears it when the status moves away, so it is
// not sent then either. Choosing 已達成 fills in today when the date is empty.
//
// Deleting a goal that still has stages is the server's 409; its sentence is
// shown in the dialog, which stays open.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import FormActions from '../../components/forms/FormActions'
import { Field, Input, Section, Select, TextArea } from '../../components/ui/primitives'
import { ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiMutation, useApiQuery } from '../../hooks/useApi'
import { DEFAULT_GOAL_STATUS, GOAL_DONE, GOAL_STATUSES, localToday } from '../../lib/roadmap'
import { blankToNull, integerOrNull } from '../../lib/rowList'

// A goal's name and code show on the roadmap and on each of its stages' pages.
const INVALIDATE = [endpoints.goals.list(), endpoints.stages.list()]

const EMPTY = {
  code: '',
  name_cn: '',
  name_en: '',
  name_alt: '',
  position: '',
  description: '',
  test: '',
  status: DEFAULT_GOAL_STATUS,
  achieved_on: '',
  remark: '',
}

function fromGoal(goal) {
  return {
    code: goal.code ?? '',
    name_cn: goal.name_cn ?? '',
    name_en: goal.name_en ?? '',
    name_alt: goal.name_alt ?? '',
    position: goal.position == null ? '' : String(goal.position),
    description: goal.description ?? '',
    test: goal.test ?? '',
    status: goal.status ?? DEFAULT_GOAL_STATUS,
    achieved_on: goal.achieved_on ?? '',
    remark: goal.remark ?? '',
  }
}

/** The form as the API's GoalWrite. A blank position and an off-status date are left out. */
function toPayload(form) {
  const body = {
    code: form.code.trim(),
    name_cn: blankToNull(form.name_cn),
    name_en: blankToNull(form.name_en),
    name_alt: blankToNull(form.name_alt),
    description: blankToNull(form.description),
    test: blankToNull(form.test),
    status: form.status,
    remark: blankToNull(form.remark),
  }
  const position = integerOrNull(form.position)
  if (position !== null) body.position = position
  if (form.status === GOAL_DONE) body.achieved_on = blankToNull(form.achieved_on)
  return body
}

export default function GoalForm() {
  const { id } = useParams()
  const isNew = id === undefined
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const existing = useApiQuery(endpoints.goals.detail(id), null, { enabled: !isNew })
  const create = useApiMutation({ method: 'POST', invalidate: INVALIDATE })
  const update = useApiMutation({ method: 'PATCH', invalidate: INVALIDATE })

  const [form, setForm] = useState(EMPTY)
  const [loaded, setLoaded] = useState(null)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const saving = create.isPending || update.isPending

  // As NoteForm: adopt the loaded row during render, keyed on its id.
  if (!isNew && existing.data && loaded?.id !== existing.data.id) {
    setLoaded(existing.data)
    setForm(fromGoal(existing.data))
  }

  const set = (field) => (event) => setForm((previous) => ({ ...previous, [field]: event.target.value }))

  function setStatus(event) {
    const status = event.target.value
    setForm((previous) => ({
      ...previous,
      status,
      achieved_on: status === GOAL_DONE && !previous.achieved_on ? localToday() : previous.achieved_on,
    }))
  }

  async function submit(event) {
    event.preventDefault()
    setError(null)
    const body = toPayload(form)
    if (!body.code) {
      setError(new Error('代號不能空白。'))
      return
    }
    if (!body.name_cn && !body.name_en && !body.name_alt) {
      setError(new Error('至少要有一個名稱。'))
      return
    }
    try {
      if (isNew) await create.mutateAsync({ url: endpoints.goals.create(), body })
      else await update.mutateAsync({ url: endpoints.goals.update(id), body })
      navigate('/roadmap')
    } catch (caught) {
      setError(caught)
    }
  }

  async function remove() {
    await fetchJson(endpoints.goals.remove(id), { method: 'DELETE' })
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/roadmap')
  }

  const stageCount = existing.data?.stages?.length ?? 0

  return (
    <form onSubmit={submit} className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-1">
        <h1 className="font-display text-2xl font-bold">{isNew ? '新增等級' : '編輯等級'}</h1>
        {!isNew && existing.data ? (
          <p className="text-sm text-text-muted">
            {existing.data.code} · {existing.data.display_name}
          </p>
        ) : null}
      </header>

      {!isNew && existing.isPending ? <Loading /> : null}
      {!isNew && existing.error ? <ErrorNote error={existing.error} /> : null}

      {isNew || existing.data ? (
        <>
          <Section title="名稱">
            <div className="grid gap-3 sm:grid-cols-4">
              <Field label="代號" hint="例如 L0。不能重複。">
                <Input value={form.code} onChange={set('code')} />
              </Field>
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

          <Section title="內容">
            <div className="space-y-3">
              <Field label="說明" hint="做到什麼程度算完成：「能……」。">
                <TextArea rows={3} value={form.description} onChange={set('description')} />
              </Field>
              <Field label="測驗" hint="用來檢驗這個等級的作品，之後可以重畫比較。">
                <TextArea rows={2} value={form.test} onChange={set('test')} />
              </Field>
            </div>
          </Section>

          <Section title="進度">
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="狀態">
                <Select value={form.status} onChange={setStatus}>
                  {GOAL_STATUSES.map((entry) => (
                    <option key={entry.value} value={entry.value}>
                      {entry.label}
                    </option>
                  ))}
                </Select>
              </Field>
              {form.status === GOAL_DONE ? (
                <Field label="達成日期">
                  <Input type="date" value={form.achieved_on} onChange={set('achieved_on')} />
                </Field>
              ) : null}
              <Field label="順序" hint="在路線圖上的位置；空白就排在最後。">
                <Input type="number" step="1" value={form.position} onChange={set('position')} />
              </Field>
            </div>
          </Section>

          <Section title="其他">
            <Field label="備註">
              <TextArea rows={3} value={form.remark} onChange={set('remark')} />
            </Field>
          </Section>

          <FormActions
            saving={saving}
            error={error}
            onCancel={() => navigate('/roadmap')}
            onDelete={isNew ? null : () => setDeleting(true)}
          />
        </>
      ) : null}

      {deleting ? (
        <DeleteDialog
          title={`刪除等級「${existing.data?.display_name ?? ''}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          {stageCount ? (
            <p>
              它還有 <strong className="tabular-nums">{stageCount}</strong> 個階段。還有階段的等級不能刪除：先把階段刪掉，或移到別的等級。
            </p>
          ) : (
            <p>刪除後就找不回來了。</p>
          )}
        </DeleteDialog>
      ) : null}
    </form>
  )
}
