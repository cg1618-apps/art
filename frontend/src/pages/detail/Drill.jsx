// Frontend: one drill, /drills/:id.
//
// Exercise's detail shape: one reading column. Above the name, its exercise's
// stage (a link to the stage's page) or 不分階段, read from the exercise; under
// it, the exercise it practises (a link to it) and its source. Then the facts -
// the round (unit × target), suggested minutes, frequency - and 記錄 (a new
// record for this drill), 開始計時 (components/timer/StartTimerButton) and 編輯.
//
// Then the Markdown instructions, the source links, the resources, the remark,
// and the records naming this drill, newest first, under their count and
// minutes. Deleting is the form's, as it is for every drill.
import { Link, useParams } from 'react-router-dom'

import { endpoints } from '../../api/endpoints'
import Markdown from '../../components/Markdown'
import RecordList from '../../components/RecordList'
import ResourceList from '../../components/ResourceList'
import StartTimerButton from '../../components/timer/StartTimerButton'
import { Chip, LinkButton, Section } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { useApiQuery } from '../../hooks/useApi'
import { drillAmount, minutesLabel, NO_STAGE_TITLE, stageTitle } from '../../lib/exercises'
import { recordMinutes } from '../../lib/records'

/** The exercise's stage as a link, or 不分階段; nothing until the exercise is read. */
function StageLine({ exerciseId }) {
  const exercise = useApiQuery(endpoints.exercises.detail(exerciseId))
  if (!exercise.data) return null
  const { stage } = exercise.data
  return (
    <p className="text-sm text-text-muted">
      {stage ? (
        <Link to={`/roadmap/stages/${stage.id}`} className="hover:text-brand hover:underline">
          {stageTitle(stage)}
        </Link>
      ) : (
        NO_STAGE_TITLE
      )}
    </p>
  )
}

function DrillRecords({ drill }) {
  const records = useApiQuery(endpoints.records.list(), { drill_id: drill.id })
  const rows = records.data ?? []
  let body
  if (records.isPending) body = <Loading />
  else if (records.error) body = <ErrorNote error={records.error} />
  else if (!rows.length) body = <p className="text-sm text-text-faint">還沒有紀錄。</p>
  else body = <RecordList records={rows} label={`「${drill.display_name}」的紀錄`} />
  const minutes = rows.reduce((total, record) => total + recordMinutes(record), 0)
  return (
    <Section
      title="紀錄"
      actions={
        records.data ? (
          <span className="text-sm tabular-nums text-text-muted">
            共 {rows.length} 筆 · {minutes} 分鐘
          </span>
        ) : null
      }
    >
      {body}
    </Section>
  )
}

export default function Drill() {
  const { id } = useParams()
  const query = useApiQuery(endpoints.drills.detail(id))
  const drill = query.data

  if (!drill) {
    if (query.isPending) return <Loading />
    if (query.error?.status === 404) {
      return <Empty action={<LinkButton to="/drills">回到練法</LinkButton>}>找不到這個練法。</Empty>
    }
    return <ErrorNote error={query.error} />
  }

  const facts = [drillAmount(drill), minutesLabel(drill.suggested_minutes), drill.frequency].filter(Boolean)

  return (
    <article className="mx-auto max-w-2xl space-y-6">
      <header className="space-y-2">
        <StageLine exerciseId={drill.exercise.id} />
        <h1 className="text-3xl font-bold">{drill.display_name}</h1>
        <div className="flex flex-wrap items-center gap-2 text-sm text-text-muted">
          <span>
            練習項目：
            <Link to={`/exercises/${drill.exercise.id}`} className="hover:text-brand hover:underline">
              {drill.exercise.display_name}
            </Link>
          </span>
          {drill.source ? (
            <Chip tone="brand" title={drill.source.description || undefined}>
              {drill.source.value}
            </Chip>
          ) : null}
        </div>
        {facts.length ? <p className="text-sm tabular-nums text-text-muted">{facts.join(' · ')}</p> : null}
        <div className="flex flex-wrap gap-2 pt-1">
          <LinkButton to={`/records/new?drill=${drill.id}`} kind="primary">
            記錄
          </LinkButton>
          <StartTimerButton drill={drill} size="md" />
          <LinkButton to={`/drills/${drill.id}/edit`}>編輯</LinkButton>
        </div>
      </header>

      {drill.instructions ? <Markdown>{drill.instructions}</Markdown> : null}

      <ResourceList resources={drill.source_links} title="來源連結" />
      <ResourceList resources={drill.resources} />

      {drill.remark ? (
        <Section title="備註">
          <p className="whitespace-pre-line text-sm leading-relaxed text-text-muted">{drill.remark}</p>
        </Section>
      ) : null}

      <DrillRecords drill={drill} />
    </article>
  )
}
