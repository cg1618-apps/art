// Frontend: add or edit a note, /notes/new and /notes/:id/edit.
//
// food's form shape: titled sections, the error above Save, Cancel back to
// where you came from, Delete through the shared dialog. Saving goes to the
// note's page.
//
// What it holds: the three name slots (at least one, `ck_note_has_a_name`),
// aliases typed into one box and split on , ， 、 and newlines (food's), the
// category and the topics through OptionPicker, the summary, the Markdown
// body, the resources as name + link rows that are added, removed and moved,
// the remark and the visibility.
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
import { Field, Input, Section, Select, TextArea } from '../../components/ui/primitives'
import { ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiMutation, useApiQuery, useOptions } from '../../hooks/useApi'
import { blankToNull, resourcesFromApi, resourcesToPayload, splitAliases } from '../../lib/rowList'
import { DEFAULT_VISIBILITY, VISIBILITIES } from '../../lib/visibility'

// A save changes the list, this note's page, and every option's in_use count.
const INVALIDATE = [endpoints.notes.list(), endpoints.options.list()]

const EMPTY = {
  name_cn: '',
  name_en: '',
  name_alt: '',
  aliases: '',
  category_id: null,
  topic_ids: [],
  summary: '',
  body: '',
  remark: '',
  visibility: DEFAULT_VISIBILITY,
  resources: [],
}

function fromNote(note) {
  return {
    name_cn: note.name_cn ?? '',
    name_en: note.name_en ?? '',
    name_alt: note.name_alt ?? '',
    aliases: (note.aliases ?? []).join('、'),
    category_id: note.category?.id ?? null,
    topic_ids: (note.topics ?? []).map((topic) => topic.id),
    summary: note.summary ?? '',
    body: note.body ?? '',
    remark: note.remark ?? '',
    visibility: note.visibility ?? DEFAULT_VISIBILITY,
    resources: resourcesFromApi(note.resources),
  }
}

/** The form as the API's NoteWrite. A resource row with no link is dropped. */
function toPayload(form) {
  return {
    name_cn: blankToNull(form.name_cn),
    name_en: blankToNull(form.name_en),
    name_alt: blankToNull(form.name_alt),
    aliases: splitAliases(form.aliases),
    category_id: form.category_id,
    topic_ids: form.topic_ids,
    summary: blankToNull(form.summary),
    body: blankToNull(form.body),
    remark: blankToNull(form.remark),
    visibility: form.visibility,
    resources: resourcesToPayload(form.resources),
  }
}

export default function NoteForm() {
  const { id } = useParams()
  const isNew = id === undefined
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const existing = useApiQuery(endpoints.notes.detail(id), null, { enabled: !isNew })
  const categories = useOptions('note_category')
  const topics = useOptions('topic')
  const create = useApiMutation({ method: 'POST', invalidate: INVALIDATE })
  const update = useApiMutation({ method: 'PATCH', invalidate: INVALIDATE })

  const [form, setForm] = useState(EMPTY)
  const [loaded, setLoaded] = useState(null)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const saving = create.isPending || update.isPending

  // Adjusting state to the loaded row during render, as React documents for
  // this case: an effect would render the empty form once first. Keyed on the
  // id, so a background refetch never throws away what is being typed.
  if (!isNew && existing.data && loaded?.id !== existing.data.id) {
    setLoaded(existing.data)
    setForm(fromNote(existing.data))
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
        ? await create.mutateAsync({ url: endpoints.notes.create(), body })
        : await update.mutateAsync({ url: endpoints.notes.update(id), body })
      navigate(`/notes/${saved.id}`)
    } catch (caught) {
      setError(caught)
    }
  }

  async function remove() {
    await fetchJson(endpoints.notes.remove(id), { method: 'DELETE' })
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/notes')
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-1">
        <h1 className="font-display text-2xl font-bold">{isNew ? '新增筆記' : '編輯筆記'}</h1>
        {!isNew && existing.data ? (
          <p className="text-sm text-text-muted">{existing.data.display_name}</p>
        ) : null}
      </header>

      {!isNew && existing.isPending ? <Loading /> : null}
      {!isNew && existing.error ? <ErrorNote error={existing.error} /> : null}

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
              <Field
                label="別名"
                className="sm:col-span-3"
                hint="用 , ， 、 或換行分開。只用來搜尋，不會顯示。"
              >
                <TextArea rows={2} value={form.aliases} onChange={set('aliases')} />
              </Field>
            </div>
          </Section>

          <Section title="分類">
            <OptionPicker
              label="分類"
              options={categories.data}
              value={form.category_id}
              onChange={setValue('category_id')}
            />
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
            <div className="space-y-3">
              <Field label="摘要" hint="一兩句話。名詞就寫它的定義；會顯示在列表裡。">
                <TextArea rows={2} value={form.summary} onChange={set('summary')} />
              </Field>
              <Field label="內文" hint="Markdown：步驟、例子、自己的理解。">
                <TextArea rows={12} value={form.body} onChange={set('body')} className="font-mono" />
              </Field>
            </div>
          </Section>

          <Section title="資源">
            <ResourceRows rows={form.resources} onChange={setValue('resources')} />
          </Section>

          <Section title="其他">
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="備註" className="sm:col-span-2">
                <TextArea rows={3} value={form.remark} onChange={set('remark')} />
              </Field>
              <Field label="可見度" hint="分享功能上線前都只有自己看得到。">
                <Select value={form.visibility} onChange={set('visibility')}>
                  {VISIBILITIES.map((entry) => (
                    <option key={entry.value} value={entry.value}>
                      {entry.label}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
          </Section>

          <FormActions
            saving={saving}
            error={error}
            onCancel={() => navigate(isNew ? '/notes' : `/notes/${id}`)}
            onDelete={isNew ? null : () => setDeleting(true)}
          />
        </>
      ) : null}

      {deleting ? (
        <DeleteDialog
          title={`刪除筆記「${existing.data?.display_name ?? ''}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。它的別名和資源會一起刪掉；分類和主題會留著。</p>
        </DeleteDialog>
      ) : null}
    </form>
  )
}
