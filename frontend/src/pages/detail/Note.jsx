// Frontend: one note, /notes/:id.
//
// One reading column, food's detail shape: the name and its other names, the
// category and topics (each a link to the library filtered by it), the
// summary, the body rendered as Markdown, the resources as links, the remark,
// then 編輯 and 刪除. A section with nothing in it is not drawn.
//
// Aliases are not shown: they exist to be searched, not read.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import Markdown from '../../components/Markdown'
import ResourceList from '../../components/ResourceList'
import { Button, Chip, LinkButton, Section } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiQuery } from '../../hooks/useApi'
import { otherNames } from '../../lib/names'
import { visibilityLabel } from '../../lib/visibility'

const INVALIDATE = [endpoints.notes.list(), endpoints.options.list()]

function OptionLink({ option, param }) {
  return (
    <Link
      to={`/notes?${param}=${option.id}`}
      title={option.description || undefined}
      className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
    >
      <Chip className="hover:border-brand hover:text-brand">{option.value}</Chip>
    </Link>
  )
}

export default function Note() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const query = useApiQuery(endpoints.notes.detail(id))
  const [deleting, setDeleting] = useState(false)
  const note = query.data

  if (!note) {
    if (query.isPending) return <Loading />
    if (query.error?.status === 404) {
      return <Empty action={<LinkButton to="/notes">回到筆記</LinkButton>}>找不到這則筆記。</Empty>
    }
    return <ErrorNote error={query.error} />
  }

  const names = otherNames(note)

  async function remove() {
    await fetchJson(endpoints.notes.remove(note.id), { method: 'DELETE' })
    // Marked stale, not refetched: this page's own read would 404 before it leaves.
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/notes')
  }

  return (
    <article className="mx-auto max-w-2xl space-y-6">
      <header className="space-y-2">
        <div className="flex flex-wrap items-baseline gap-2">
          <h1 className="text-3xl font-bold">{note.display_name}</h1>
          {note.category ? (
            <Link
              to={`/notes?category=${note.category.id}`}
              title={note.category.description || undefined}
              className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
            >
              <Chip tone="brand">{note.category.value}</Chip>
            </Link>
          ) : null}
          {note.visibility && note.visibility !== 'private' ? (
            <Chip tone="warn">{visibilityLabel(note.visibility)}</Chip>
          ) : null}
        </div>
        {names.length ? <p className="text-sm text-text-muted">{names.join(' · ')}</p> : null}
        {note.topics?.length ? (
          <div className="flex flex-wrap gap-1">
            {note.topics.map((topic) => (
              <OptionLink key={topic.id} option={topic} param="topic" />
            ))}
          </div>
        ) : null}
      </header>

      {note.summary ? <p className="font-display text-lg leading-relaxed text-text">{note.summary}</p> : null}

      {note.body ? <Markdown>{note.body}</Markdown> : null}

      <ResourceList resources={note.resources} />

      {note.remark ? (
        <Section title="備註">
          <p className="whitespace-pre-line text-sm leading-relaxed text-text-muted">{note.remark}</p>
        </Section>
      ) : null}

      <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
        <LinkButton to={`/notes/${note.id}/edit`} kind="primary">
          編輯
        </LinkButton>
        <Button kind="danger" className="ml-auto" onClick={() => setDeleting(true)}>
          刪除
        </Button>
      </div>

      {deleting ? (
        <DeleteDialog
          title={`刪除筆記「${note.display_name}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。它的別名和資源會一起刪掉；分類和主題會留著。</p>
        </DeleteDialog>
      ) : null}
    </article>
  )
}
