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
import { Button, Chip, LinkButton, Section } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiQuery } from '../../hooks/useApi'
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

const isWebLink = (url) => /^https?:\/\//i.test(url ?? '')

// A resource's words: its name, else the link's host, else the link.
function resourceLabel(resource) {
  if (resource.name) return resource.name
  try {
    return new URL(resource.url).host || resource.url
  } catch {
    return resource.url
  }
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

  const otherNames = [note.name_cn, note.name_en, note.name_alt].filter(
    (name) => name && name !== note.display_name,
  )

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
        {otherNames.length ? <p className="text-sm text-text-muted">{otherNames.join(' · ')}</p> : null}
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

      {note.resources?.length ? (
        <Section title="資源">
          <ul className="space-y-1">
            {note.resources.map((resource) => (
              <li key={resource.id ?? resource.url}>
                {isWebLink(resource.url) ? (
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand hover:underline"
                  >
                    {resourceLabel(resource)} ↗
                  </a>
                ) : (
                  // Not an http(s) link - a javascript: URL among them - so it
                  // is shown as text, as the Markdown renderer would leave it.
                  <span className="text-text-muted">
                    {resource.name ? `${resource.name}: ` : ''}
                    {resource.url}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

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
