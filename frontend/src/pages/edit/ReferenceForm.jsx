// Frontend: add or edit a reference, /references/new and /references/:id/edit.
//
// NoteForm's shape: titled sections, the error above Save, Cancel back to
// where you came from, Delete through the shared dialog. Saving goes to the
// reference's page.
//
// What it holds: the name and the link (both required; a link typed without
// http:// or https:// is stored with https://), the groups through
// OptionPicker, and the notes in Markdown.
//
// An edit is a PATCH carrying every field, the group list included: a list
// sent replaces the old one whole, which is what the form shows.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import FormActions from '../../components/forms/FormActions'
import OptionPicker from '../../components/forms/OptionPicker'
import { Field, Input, Section, TextArea } from '../../components/ui/primitives'
import { ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiMutation, useApiQuery, useOptions } from '../../hooks/useApi'
import { blankToNull } from '../../lib/rowList'

// A save changes the list, this reference's page, and every group's in_use count.
const INVALIDATE = [endpoints.references.list(), endpoints.options.list()]

const EMPTY = { name: '', url: '', group_ids: [], notes: '' }

function fromReference(reference) {
  return {
    name: reference.name ?? '',
    url: reference.url ?? '',
    group_ids: (reference.groups ?? []).map((group) => group.id),
    notes: reference.notes ?? '',
  }
}

/** The form as the API's ReferenceWrite. */
function toPayload(form) {
  return {
    name: blankToNull(form.name),
    url: blankToNull(form.url),
    group_ids: form.group_ids,
    notes: blankToNull(form.notes),
  }
}

export default function ReferenceForm() {
  const { id } = useParams()
  const isNew = id === undefined
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const existing = useApiQuery(endpoints.references.detail(id), null, { enabled: !isNew })
  const groups = useOptions('reference_group')
  const create = useApiMutation({ method: 'POST', invalidate: INVALIDATE })
  const update = useApiMutation({ method: 'PATCH', invalidate: INVALIDATE })

  const [form, setForm] = useState(EMPTY)
  const [loaded, setLoaded] = useState(null)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const saving = create.isPending || update.isPending

  // Adjusting state to the loaded row during render, as NoteForm does: keyed
  // on the id, so a background refetch never throws away what is being typed.
  if (!isNew && existing.data && loaded?.id !== existing.data.id) {
    setLoaded(existing.data)
    setForm(fromReference(existing.data))
  }

  const set = (field) => (event) => setForm((previous) => ({ ...previous, [field]: event.target.value }))
  const setValue = (field) => (value) => setForm((previous) => ({ ...previous, [field]: value }))

  async function submit(event) {
    event.preventDefault()
    setError(null)
    const body = toPayload(form)
    if (!body.name) {
      setError(new Error('請填寫名稱。'))
      return
    }
    if (!body.url) {
      setError(new Error('請填寫連結。'))
      return
    }
    try {
      const saved = isNew
        ? await create.mutateAsync({ url: endpoints.references.create(), body })
        : await update.mutateAsync({ url: endpoints.references.update(id), body })
      navigate(`/references/${saved.id}`)
    } catch (caught) {
      setError(caught)
    }
  }

  async function remove() {
    await fetchJson(endpoints.references.remove(id), { method: 'DELETE' })
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/references')
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-1">
        <h1 className="font-display text-2xl font-bold">{isNew ? '新增參考' : '編輯參考'}</h1>
        {!isNew && existing.data ? (
          <p className="text-sm text-text-muted">{existing.data.name}</p>
        ) : null}
      </header>

      {!isNew && existing.isPending ? <Loading /> : null}
      {!isNew && existing.error ? <ErrorNote error={existing.error} /> : null}

      {isNew || existing.data ? (
        <>
          <Section title="連結">
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="名稱">
                <Input value={form.name} onChange={set('name')} />
              </Field>
              <Field label="網址" hint="沒有 http:// 或 https:// 時會自動加上 https://。">
                <Input value={form.url} onChange={set('url')} inputMode="url" />
              </Field>
            </div>
          </Section>

          <Section title="參考分組">
            <OptionPicker
              label="參考分組"
              multiple
              options={groups.data}
              value={form.group_ids}
              onChange={setValue('group_ids')}
              empty="還沒有任何分組，可以到選項頁新增。"
            />
          </Section>

          <Section title="筆記">
            <Field label="筆記" hint="Markdown：這個參考好在哪裡、要看什麼。">
              <TextArea rows={8} value={form.notes} onChange={set('notes')} className="font-mono" />
            </Field>
          </Section>

          <FormActions
            saving={saving}
            error={error}
            onCancel={() => navigate(isNew ? '/references' : `/references/${id}`)}
            onDelete={isNew ? null : () => setDeleting(true)}
          />
        </>
      ) : null}

      {deleting ? (
        <DeleteDialog
          title={`刪除參考「${existing.data?.name ?? ''}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。只刪掉這筆參考和它的筆記；分組會留著。</p>
        </DeleteDialog>
      ) : null}
    </form>
  )
}
