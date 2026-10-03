// Frontend: one stage, /roadmap/stages/:id.
//
// Note's detail shape: one reading column. Above the name, the stage's number
// and the goal it belongs to (a link back to the roadmap); then its status and
// the date it was passed, the focus (description), the test piece, the
// resources as links, the remark; then the stage's exercises (each a link to
// its page) and its test records, newest first; then 編輯 and 刪除. A section
// with nothing in it is not drawn, except those two lists, which say they are
// empty: an empty one is a gap in the plan, not a missing field.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import RecordList from '../../components/RecordList'
import ResourceList from '../../components/ResourceList'
import { Button, Chip, LinkButton, Section } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiQuery } from '../../hooks/useApi'
import { otherNames } from '../../lib/names'
import { TEST_KIND } from '../../lib/records'
import { stageStatusLabel, stageStatusTone } from '../../lib/roadmap'

const INVALIDATE = [endpoints.goals.list(), endpoints.stages.list()]

function StageExercises({ stageId }) {
  const exercises = useApiQuery(endpoints.exercises.list(), { stage_id: stageId })
  let body
  if (exercises.isPending) body = <Loading />
  else if (exercises.error) body = <ErrorNote error={exercises.error} />
  else if (!exercises.data.length) body = <p className="text-sm text-text-faint">這個階段還沒有練習項目。</p>
  else
    body = (
      <ul className="space-y-1" aria-label="這個階段的練習">
        {exercises.data.map((exercise) => (
          <li key={exercise.id} className="flex flex-wrap items-baseline gap-x-2">
            <Link to={`/exercises/${exercise.id}`} className="font-medium text-text hover:text-brand hover:underline">
              {exercise.display_name}
            </Link>
            <span className="text-xs tabular-nums text-text-faint">
              {exercise.drill_count ?? 0} 個練法 · {exercise.total_minutes ?? 0} 分鐘
            </span>
          </li>
        ))}
      </ul>
    )
  return <Section title="練習">{body}</Section>
}

function StageTests({ stageId }) {
  const records = useApiQuery(endpoints.records.list(), { stage_id: stageId, kind: TEST_KIND })
  let body
  if (records.isPending) body = <Loading />
  else if (records.error) body = <ErrorNote error={records.error} />
  else if (!records.data.length) body = <p className="text-sm text-text-faint">還沒有測驗紀錄。</p>
  else body = <RecordList records={records.data} label="這個階段的測驗紀錄" />
  return <Section title="測驗紀錄">{body}</Section>
}

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

  const names = otherNames(stage)

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
        {names.length ? <p className="text-sm text-text-muted">{names.join(' · ')}</p> : null}
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

      <StageExercises stageId={stage.id} />

      <StageTests stageId={stage.id} />

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
