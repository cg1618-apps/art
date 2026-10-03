// Frontend: one reference, /references/:id.
//
// Note's detail shape, one reading column: the name, the link itself (opened
// in a new tab), the groups (each a link to the library filtered by it), the
// notes rendered as Markdown, then 編輯 and 刪除. A section with nothing in it
// is not drawn.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import Markdown from '../../components/Markdown'
import { Button, Chip, LinkButton } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiQuery } from '../../hooks/useApi'
import { isWebLink } from '../../lib/links'

const INVALIDATE = [endpoints.references.list(), endpoints.options.list()]

export default function Reference() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const query = useApiQuery(endpoints.references.detail(id))
  const [deleting, setDeleting] = useState(false)
  const reference = query.data

  if (!reference) {
    if (query.isPending) return <Loading />
    if (query.error?.status === 404) {
      return <Empty action={<LinkButton to="/references">回到參考</LinkButton>}>找不到這個參考。</Empty>
    }
    return <ErrorNote error={query.error} />
  }

  async function remove() {
    await fetchJson(endpoints.references.remove(reference.id), { method: 'DELETE' })
    // Marked stale, not refetched: this page's own read would 404 before it leaves.
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/references')
  }

  return (
    <article className="mx-auto max-w-2xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold">{reference.name}</h1>
        <p className="break-all text-sm">
          {isWebLink(reference.url) ? (
            <a href={reference.url} target="_blank" rel="noopener noreferrer" className="text-brand hover:underline">
              {reference.url} ↗
            </a>
          ) : (
            <span className="text-text-muted">{reference.url}</span>
          )}
        </p>
        {reference.groups?.length ? (
          <div className="flex flex-wrap gap-1">
            {reference.groups.map((group) => (
              <Link
                key={group.id}
                to={`/references?group=${group.id}`}
                title={group.description || undefined}
                className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              >
                <Chip className="hover:border-brand hover:text-brand">{group.value}</Chip>
              </Link>
            ))}
          </div>
        ) : null}
      </header>

      {reference.notes ? <Markdown>{reference.notes}</Markdown> : null}

      <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
        <LinkButton to={`/references/${reference.id}/edit`} kind="primary">
          編輯
        </LinkButton>
        <Button kind="danger" className="ml-auto" onClick={() => setDeleting(true)}>
          刪除
        </Button>
      </div>

      {deleting ? (
        <DeleteDialog
          title={`刪除參考「${reference.name}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。只刪掉這筆參考和它的筆記；分組會留著。</p>
        </DeleteDialog>
      ) : null}
    </article>
  )
}
