// Frontend: one stage, /roadmap/stages/:id.
//
// Note's detail shape: one reading column. Above the name, the stage's number
// and the goal it belongs to (a link back to the roadmap); then its status and
// the date it was passed, the focus (description), the test piece, the
// resources as links, the remark, then 編輯 and 刪除. A section with nothing
// in it is not drawn.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import ResourceList from '../../components/ResourceList'
import { Button, Chip, LinkButton, Section } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiQuery } from '../../hooks/useApi'
import { stageStatusLabel, stageStatusTone } from '../../lib/roadmap'

const INVALIDATE = [endpoints.goals.list(), endpoints.stages.list()]

export default function Stage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const query = useApiQuery(endpoints.stages.detail(id))
  const [deleting, setDeleting] = useState(false)
  const stage = query.data

  if (!stage) {
    if (query.isPending) return <Loading />
    if (query.error?.status === 404) {
      return <Empty action={<LinkButton to="/roadmap">回到路線圖</LinkButton>}>找不到這個階段。</Empty>
    }
    return <ErrorNote error={query.error} />
  }

  const otherNames = [stage.name_cn, stage.name_en, stage.name_alt].filter(
    (name) => name && name !== stage.display_name,
  )

  async function remove() {
    await fetchJson(endpoints.stages.remove(stage.id), { method: 'DELETE' })
    // Marked stale, not refetched: this page's own read would 404 before it leaves.
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/roadmap')
  }

  return (
    <article className="mx-auto max-w-2xl space-y-6">
      <header className="space-y-2">
        <p className="text-sm text-text-muted">
          <span className="tabular-nums">階段 {stage.number}</span>
          {stage.goal ? (
            <>
              {' · '}
              <Link to="/roadmap" className="hover:text-brand hover:underline">
                {stage.goal.code} {stage.goal.display_name}
              </Link>
            </>
          ) : null}
        </p>
        <div className="flex flex-wrap items-baseline gap-2">
          <h1 className="text-3xl font-bold">{stage.display_name}</h1>
          <Chip tone={stageStatusTone(stage.status)}>{stageStatusLabel(stage.status)}</Chip>
          {stage.passed_on ? <span className="text-sm text-text-faint">{stage.passed_on} 通過</span> : null}
        </div>
        {otherNames.length ? <p className="text-sm text-text-muted">{otherNames.join(' · ')}</p> : null}
      </header>

      {stage.description ? (
        <Section title="重點">
          <p className="whitespace-pre-line font-display text-lg leading-relaxed text-text">{stage.description}</p>
        </Section>
      ) : null}

      {stage.test ? (
        <Section title="測驗">
          <p className="whitespace-pre-line leading-relaxed text-text">{stage.test}</p>
        </Section>
      ) : null}

      <ResourceList resources={stage.resources} />

      {stage.remark ? (
        <Section title="備註">
          <p className="whitespace-pre-line text-sm leading-relaxed text-text-muted">{stage.remark}</p>
        </Section>
      ) : null}

      <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
        <LinkButton to={`/roadmap/stages/${stage.id}/edit`} kind="primary">
          編輯
        </LinkButton>
        <Button kind="danger" className="ml-auto" onClick={() => setDeleting(true)}>
          刪除
        </Button>
      </div>

      {deleting ? (
        <DeleteDialog
          title={`刪除階段「${stage.display_name}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。它的資源會一起刪掉；之後的階段編號會往前移。</p>
        </DeleteDialog>
      ) : null}
    </article>
  )
}
