// Frontend: the roadmap, /roadmap.
//
// Every goal - a level - in roadmap order: its code, name, status, what "done"
// means (description) and its test piece. Under each, its stages as rows:
// number, name, status, test. One read, GET /api/goals, carries all of it.
//
// The CURRENT STAGE is the first stage, across every goal in order, that is
// not passed (lib/roadmap.js). It is marked with aria-current="step" and drawn
// in the brand colour, so the page answers "what do I practise today" at a
// glance. Goal status is not consulted: status is set by hand, and a level may
// be passed on its test before every stage is ticked.
//
// A stage's status changes from its row through a small select, a PATCH of
// { status } alone - with passed_on = today (the browser's date) when it
// becomes passed; the server clears the date when it moves away. ↑ / ↓ move a
// stage inside its goal by PATCHing positions: the goal's stages are
// renumbered 0..n-1 in their new order and only the ones whose position
// changed are sent, so the result does not depend on what numbers the seed or
// an earlier edit left behind.
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchJson, jsonBody } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import { Button, Chip, LinkButton, Select } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { invalidateResources, useApiQuery } from '../../hooks/useApi'
import { cx } from '../../lib/cx'
import {
  currentStageId,
  goalStatusLabel,
  goalStatusTone,
  localToday,
  STAGE_DONE,
  STAGE_STATUSES,
} from '../../lib/roadmap'
import { rowsReducer } from '../../lib/rowList'

// A stage change shows on the roadmap and on that stage's own page.
const INVALIDATE = [endpoints.goals.list(), endpoints.stages.list()]

function StageRow({ stage, current, first, last, busy, onStatus, onMove }) {
  const [error, setError] = useState(null)

  async function run(action) {
    setError(null)
    try {
      await action()
    } catch (caught) {
      setError(caught)
    }
  }

  return (
    <li
      aria-current={current ? 'step' : undefined}
      className={cx(
        'space-y-2 border-t border-border px-3 py-2.5 first:border-t-0',
        current && 'border-l-4 border-l-brand bg-brand-soft',
      )}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <span className="w-6 shrink-0 text-right font-mono text-sm tabular-nums text-text-faint">
          {stage.number}
        </span>
        <div className="min-w-0 flex-1 basis-48">
          <div className="flex flex-wrap items-baseline gap-2">
            <Link
              to={`/roadmap/stages/${stage.id}`}
              className={cx(
                'font-medium hover:text-brand hover:underline',
                current ? 'text-brand' : stage.status === STAGE_DONE ? 'text-text-muted' : 'text-text',
              )}
            >
              {stage.display_name}
            </Link>
            {current ? <Chip tone="brand">目前</Chip> : null}
          </div>
          {stage.test ? <p className="text-sm text-text-muted">測驗：{stage.test}</p> : null}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Select
            aria-label={`「${stage.display_name}」的狀態`}
            value={stage.status}
            disabled={busy}
            onChange={(event) => run(() => onStatus(event.target.value))}
            className="w-auto py-1 text-xs"
          >
            {STAGE_STATUSES.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label}
              </option>
            ))}
          </Select>
          <Button
            size="sm"
            kind="ghost"
            aria-label={`上移「${stage.display_name}」`}
            title="上移"
            disabled={busy || first}
            onClick={() => run(() => onMove(-1))}
          >
            ↑
          </Button>
          <Button
            size="sm"
            kind="ghost"
            aria-label={`下移「${stage.display_name}」`}
            title="下移"
            disabled={busy || last}
            onClick={() => run(() => onMove(1))}
          >
            ↓
          </Button>
        </div>
      </div>
      {error ? <ErrorNote error={error} /> : null}
    </li>
  )
}

function GoalBlock({ goal, currentId, busy, onStatus, onMove }) {
  const headingId = `goal-${goal.id}`
  const stages = goal.stages ?? []
  return (
    <section aria-labelledby={headingId} className="overflow-hidden rounded-lg border border-border bg-surface">
      <div className="space-y-2 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Chip className="font-mono">{goal.code}</Chip>
          <h2 id={headingId} className="text-xl font-bold">
            {goal.display_name}
          </h2>
          <Chip tone={goalStatusTone(goal.status)}>{goalStatusLabel(goal.status)}</Chip>
          {goal.achieved_on ? <span className="text-xs text-text-faint">{goal.achieved_on}</span> : null}
          <LinkButton
            to={`/roadmap/goals/${goal.id}/edit`}
            size="sm"
            kind="ghost"
            className="ml-auto"
            aria-label={`編輯等級「${goal.display_name}」`}
          >
            編輯
          </LinkButton>
        </div>
        {goal.description ? <p className="leading-relaxed text-text">{goal.description}</p> : null}
        {goal.test ? (
          <p className="text-sm text-text-muted">
            <span className="font-medium">測驗：</span>
            {goal.test}
          </p>
        ) : null}
      </div>

      <div className="border-t border-border bg-canvas/40">
        {stages.length ? (
          <ol aria-label={`${goal.display_name}的階段`}>
            {stages.map((stage, index) => (
              <StageRow
                key={stage.id}
                stage={stage}
                current={stage.id === currentId}
                first={index === 0}
                last={index === stages.length - 1}
                busy={busy}
                onStatus={(status) => onStatus(stage, status)}
                onMove={(step) => onMove(goal, index, index + step)}
              />
            ))}
          </ol>
        ) : (
          <p className="px-3 py-2.5 text-sm text-text-faint">還沒有階段。</p>
        )}
        <div className="border-t border-border px-3 py-2">
          <LinkButton to={`/roadmap/stages/new?goal=${goal.id}`} size="sm">
            ＋ 新增階段
          </LinkButton>
        </div>
      </div>
    </section>
  )
}

export default function Roadmap() {
  const queryClient = useQueryClient()
  const goals = useApiQuery(endpoints.goals.list())
  const [busy, setBusy] = useState(false)

  async function write(requests) {
    setBusy(true)
    try {
      for (const { id, body } of requests) {
        await fetchJson(endpoints.stages.update(id), { method: 'PATCH', ...jsonBody(body) })
      }
    } finally {
      await invalidateResources(queryClient, INVALIDATE)
      setBusy(false)
    }
  }

  function setStatus(stage, status) {
    const body = status === STAGE_DONE ? { status, passed_on: localToday() } : { status }
    return write([{ id: stage.id, body }])
  }

  function move(goal, from, to) {
    const order = rowsReducer(goal.stages, { type: 'move', from, to })
    const changed = order
      .map((stage, position) => ({ id: stage.id, position, was: stage.position }))
      .filter((entry) => entry.position !== entry.was)
      .map(({ id, position }) => ({ id, body: { position } }))
    return write(changed)
  }

  let body
  if (goals.isPending) body = <Loading />
  else if (goals.error) body = <ErrorNote error={goals.error} />
  else if (!goals.data.length)
    body = (
      <Empty action={<LinkButton to="/roadmap/goals/new">新增等級</LinkButton>}>還沒有任何等級。</Empty>
    )
  else {
    const currentId = currentStageId(goals.data)
    body = (
      <div className="space-y-5">
        {goals.data.map((goal) => (
          <GoalBlock
            key={goal.id}
            goal={goal}
            currentId={currentId}
            busy={busy}
            onStatus={setStatus}
            onMove={move}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold">路線圖</h1>
          <p className="text-sm text-text-muted">每個等級以測驗作品結束；目前的階段是第一個還沒通過的。</p>
        </div>
        <LinkButton to="/roadmap/goals/new" kind="primary">
          新增等級
        </LinkButton>
      </header>
      {body}
    </div>
  )
}
