// Frontend: one exercise, /exercises/:id.
//
// Note's detail shape: one reading column. Above the name, the stage it
// belongs to (a link to the stage's page) or 不分階段; then its other names
// and topics (each a link to the library filtered by it), the description,
// the resources, the remark.
//
// Then its drills as cards - the name linking to the drill's own page, source,
// the round (unit × target), suggested minutes, frequency, the Markdown
// instructions, the source links and resources - each with 記錄 (a new record
// for that drill), 開始計時 (components/timer/StartTimerButton) and 編輯; and
// the exercise's records, directly or through a drill, newest first, under the
// total minutes. 編輯 and 刪除 close the page; deleting an exercise that still
// has drills or records is the server's 409, shown in the dialog.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { fetchJson } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import Markdown from '../../components/Markdown'
import RecordList from '../../components/RecordList'
import ResourceList from '../../components/ResourceList'
import StartTimerButton from '../../components/timer/StartTimerButton'
import { Button, Card, Chip, LinkButton, Section } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiQuery } from '../../hooks/useApi'
import { drillAmount, minutesLabel, NO_STAGE_TITLE, stageTitle } from '../../lib/exercises'
import { otherNames } from '../../lib/names'

const INVALIDATE = [endpoints.exercises.list(), endpoints.options.list()]

function DrillCard({ drill }) {
  const facts = [drillAmount(drill), minutesLabel(drill.suggested_minutes), drill.frequency].filter(Boolean)
  return (
    <Card className="space-y-3">
      <div className="flex flex-wrap items-baseline gap-2">
        <h3 className="font-display text-lg font-bold">
          <Link to={`/drills/${drill.id}`} className="hover:text-brand hover:underline">
            {drill.display_name}
          </Link>
        </h3>
        {drill.source ? (
          <Chip tone="brand" title={drill.source.description || undefined}>
            {drill.source.value}
          </Chip>
        ) : null}
        <span className="ml-auto flex gap-1">
          <LinkButton
            to={`/records/new?drill=${drill.id}`}
            size="sm"
            kind="primary"
            aria-label={`記錄「${drill.display_name}」`}
          >
            記錄
          </LinkButton>
          <StartTimerButton drill={drill} />
          <LinkButton
            to={`/drills/${drill.id}/edit`}
            size="sm"
            kind="ghost"
            aria-label={`編輯練法「${drill.display_name}」`}
          >
            編輯
          </LinkButton>
        </span>
      </div>
      {facts.length ? <p className="text-sm tabular-nums text-text-muted">{facts.join(' · ')}</p> : null}
      {drill.instructions ? <Markdown>{drill.instructions}</Markdown> : null}
      <ResourceList resources={drill.source_links} title="來源連結" as="h4" />
      <ResourceList resources={drill.resources} as="h4" />
      {drill.remark ? <p className="whitespace-pre-line text-sm text-text-muted">{drill.remark}</p> : null}
    </Card>
  )
}

function ExerciseRecords({ exercise }) {
  const records = useApiQuery(endpoints.records.list(), { exercise_id: exercise.id })
  let body
  if (records.isPending) body = <Loading />
  else if (records.error) body = <ErrorNote error={records.error} />
  else if (!records.data.length) body = <p className="text-sm text-text-faint">還沒有紀錄。</p>
  else body = <RecordList records={records.data} label={`「${exercise.display_name}」的紀錄`} />
  return (
    <Section
      title="紀錄"
      actions={
        <span className="text-sm tabular-nums text-text-muted">
          共 {exercise.record_count ?? 0} 筆 · {exercise.total_minutes ?? 0} 分鐘
        </span>
      }
    >
      {body}
    </Section>
  )
}

export default function Exercise() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const query = useApiQuery(endpoints.exercises.detail(id))
  const [deleting, setDeleting] = useState(false)
  const exercise = query.data

  if (!exercise) {
    if (query.isPending) return <Loading />
    if (query.error?.status === 404) {
      return <Empty action={<LinkButton to="/exercises">回到練習</LinkButton>}>找不到這個練習項目。</Empty>
    }
    return <ErrorNote error={query.error} />
  }

  const names = otherNames(exercise)
  const drills = exercise.drills ?? []

  async function remove() {
    await fetchJson(endpoints.exercises.remove(exercise.id), { method: 'DELETE' })
    // Marked stale, not refetched: this page's own read would 404 before it leaves.
    invalidateResources(queryClient, INVALIDATE, { refetchType: 'none' })
    navigate('/exercises')
  }

  return (
    <article className="mx-auto max-w-2xl space-y-6">
      <header className="space-y-2">
        <p className="text-sm text-text-muted">
          {exercise.stage ? (
            <Link to={`/roadmap/stages/${exercise.stage.id}`} className="hover:text-brand hover:underline">
              {stageTitle(exercise.stage)}
            </Link>
          ) : (
            NO_STAGE_TITLE
          )}
        </p>
        <h1 className="text-3xl font-bold">{exercise.display_name}</h1>
        {names.length ? <p className="text-sm text-text-muted">{names.join(' · ')}</p> : null}
        {exercise.topics?.length ? (
          <div className="flex flex-wrap gap-1">
            {exercise.topics.map((topic) => (
              <Link
                key={topic.id}
                to={`/exercises?topic=${topic.id}`}
                title={topic.description || undefined}
                className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              >
                <Chip className="hover:border-brand hover:text-brand">{topic.value}</Chip>
              </Link>
            ))}
          </div>
        ) : null}
      </header>

      {exercise.description ? (
        <p className="whitespace-pre-line font-display text-lg leading-relaxed text-text">{exercise.description}</p>
      ) : null}

      <ResourceList resources={exercise.resources} />

      {exercise.remark ? (
        <Section title="備註">
          <p className="whitespace-pre-line text-sm leading-relaxed text-text-muted">{exercise.remark}</p>
        </Section>
      ) : null}

      <Section
        title="練法"
        actions={
          <LinkButton to={`/drills/new?exercise=${exercise.id}`} size="sm">
            ＋ 新增練法
          </LinkButton>
        }
      >
        {drills.length ? (
          <ul className="space-y-3" aria-label="練法">
            {drills.map((drill) => (
              <li key={drill.id}>
                <DrillCard drill={drill} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-text-faint">還沒有練法。</p>
        )}
        <LinkButton to={`/records/new?exercise=${exercise.id}`} size="sm">
          記錄這個練習（不指定練法）
        </LinkButton>
      </Section>

      <ExerciseRecords exercise={exercise} />

      <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4">
        <LinkButton to={`/exercises/${exercise.id}/edit`} kind="primary">
          編輯
        </LinkButton>
        <Button kind="danger" className="ml-auto" onClick={() => setDeleting(true)}>
          刪除
        </Button>
      </div>

      {deleting ? (
        <DeleteDialog
          title={`刪除練習項目「${exercise.display_name}」？`}
          onConfirm={remove}
          onClose={() => setDeleting(false)}
        >
          <p>刪除後就找不回來了。它的別名和資源會一起刪掉；還有練法或紀錄的練習項目不能刪除。</p>
        </DeleteDialog>
      ) : null}
    </article>
  )
}
