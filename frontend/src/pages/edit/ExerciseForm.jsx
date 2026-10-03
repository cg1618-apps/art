// Frontend: add or edit an exercise, /exercises/new and /exercises/:id/edit.
//
// NoteForm's shape. What it holds: the three name slots (at least one,
// `ck_exercise_has_a_name`), aliases in one box, the stage it belongs to
// (components/forms/RoadmapSelect; none for what is practised at every
// level), the topics through OptionPicker, the description, the resources as
// name + link rows, and the remark. Drills are edited on their own form,
// reached from the exercise's page.
//
// An edit is a PATCH carrying every field, lists included: a list sent
// replaces the old one whole, which is what the form shows.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import FormActions from '../../components/forms/FormActions'
import OptionPicker from '../../components/forms/OptionPicker'
import ResourceRows from '../../components/forms/ResourceRows'
import RoadmapSelect from '../../components/forms/RoadmapSelect'
import { Field, Input, Section, TextArea } from '../../components/ui/primitives'
import { ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiMutation, useApiQuery, useOptions } from '../../hooks/useApi'
import { parseTarget, targetValue } from '../../lib/roadmap'
import { blankToNull, resourcesFromApi, resourcesToPayload, splitAliases } from '../../lib/rowList'

// A save changes the library, this exercise's page, its drills in the drill
// library (their exercise's name, stage and topics), its stage's page and
// every topic's in_use count.
const INVALIDATE = [
  endpoints.exercises.list(),
  endpoints.drills.list(),
  endpoints.stages.list(),
  endpoints.options.list(),
]

const EMPTY = {
  name_cn: '',
  name_en: '',
  name_alt: '',
  aliases: '',
  stage: '',
  topic_ids: [],
  description: '',
  remark: '',
  resources: [],
}

function fromExercise(exercise) {
  return {
    name_cn: exercise.name_cn ?? '',
    name_en: exercise.name_en ?? '',
    name_alt: exercise.name_alt ?? '',
    aliases: (exercise.aliases ?? []).join('、'),
    stage: exercise.stage ? targetValue('stage', exercise.stage.id) : '',
    topic_ids: (exercise.topics ?? []).map((topic) => topic.id),
    description: exercise.description ?? '',
    remark: exercise.remark ?? '',
    resources: resourcesFromApi(exercise.resources),
  }
}

/** The form as the API's ExerciseWrite. */
function toPayload(form) {
  return {
    name_cn: blankToNull(form.name_cn),
    name_en: blankToNull(form.name_en),
    name_alt: blankToNull(form.name_alt),
    aliases: splitAliases(form.aliases),
    stage_id: parseTarget(form.stage).stage_id,
    topic_ids: form.topic_ids,
    description: blankToNull(form.description),
    remark: blankToNull(form.remark),
    resources: resourcesToPayload(form.resources),
  }
}

export default function ExerciseForm() {
  const { id } = useParams()
  const isNew = id === undefined
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const existing = useApiQuery(endpoints.exercises.detail(id), null, { enabled: !isNew })
  const goals = useApiQuery(endpoints.goals.list())
  const topics = useOptions('topic')
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
    setForm(fromExercise(existing.data))
  }

  const set = (field) => (event) => setForm((previous) => ({ ...previous, [field]: event.target.value }))
  const setValue = (field) => (value) => setForm((previous) => ({ ...previous, [field]: value }))

  async function submit(event) {
    event.preventDefault()
    setError(null)
    const body = toPayload(form)
    if (!body.name_cn && !body.name_en && !body.name_alt) {
      setError(new Error('至少要有一個名稱。'))
      return
    }
    try {
      const saved = isNew
        ? await create.mutateAsync({ url: endpoints.exercises.create(), body })
        : await update.mutateAsync({ url: endpoints.exercises.update(id), body })
      navigate(`/exercises/${saved.id}`)
    } catch (caught) {
      setError(caught)
    }
  }

  async function remove() {
    await fetchJson(endpoints.exercises.remove(id), { method: 'DELETE' })
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/exercises')
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-1">
        <h1 className="font-display text-2xl font-bold">{isNew ? '新增練習項目' : '編輯練習項目'}</h1>
        {!isNew && existing.data ? <p className="text-sm text-text-muted">{existing.data.display_name}</p> : null}
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
              <Field label="別名" className="sm:col-span-3" hint="用 , ， 、 或換行分開。只用來搜尋，不會顯示。">
                <TextArea rows={2} value={form.aliases} onChange={set('aliases')} />
              </Field>
            </div>
          </Section>

          <Section title="階段">
            <Field label="階段" hint="每個等級都練的（暖身、動態速寫）就不分階段。">
              <RoadmapSelect
                goals={goals.data}
                value={form.stage}
                onChange={setValue('stage')}
                placeholder="不分階段"
              />
            </Field>
          </Section>

          <Section title="主題">
            <OptionPicker
              label="主題"
              multiple
              options={topics.data}
              value={form.topic_ids}
              onChange={setValue('topic_ids')}
            />
          </Section>

          <Section title="內容">
            <Field label="說明" hint="練的是什麼。會顯示在列表裡。">
              <TextArea rows={3} value={form.description} onChange={set('description')} />
            </Field>
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
            onCancel={() => navigate(isNew ? '/exercises' : `/exercises/${id}`)}
            onDelete={isNew ? null : () => setDeleting(true)}
          />
        </>
      ) : null}

      {deleting ? (
        <DeleteDialog
          title={`刪除練習項目「${existing.data?.display_name ?? ''}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。它的別名和資源會一起刪掉；還有練法或紀錄的練習項目不能刪除。</p>
        </DeleteDialog>
      ) : null}
    </form>
  )
}
