// Frontend: records as rows - the records page's days, an exercise's records,
// a stage's test records.
//
// Each row: what was practised (the exercise, a link to it, and the drill when
// it has a name of its own), the kind when it is not plain practice, what a
// test tests, the minutes, the location / method / tool, the notes and the
// reference links, and 編輯. There is no record page of its own: a record is
// read in its row and changed in its form. Field access is lib/records.js.
//
//   records   [Record]
//   label     the list's accessible name
//   showDate  whether each row states its date (off inside a day's group)
import { Link } from 'react-router-dom'

import { minutesLabel } from '../lib/exercises'
import {
  recordDrillName,
  recordExercise,
  recordHasDuration,
  recordKindLabel,
  recordMinutes,
  recordNotes,
  recordOptions,
  recordReferences,
  recordTestTarget,
  TEST_KIND,
  DEFAULT_RECORD_KIND,
} from '../lib/records'
import { Chip, LinkButton } from './ui/primitives'

const isWebLink = (url) => /^https?:\/\//i.test(url ?? '')

function RecordRow({ record, showDate }) {
  const exercise = recordExercise(record)
  const drillName = recordDrillName(record)
  const target = recordTestTarget(record)
  const notes = recordNotes(record)
  const references = recordReferences(record)
  return (
    <div className="space-y-1.5 rounded-lg border border-border bg-surface p-3">
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        {showDate ? <span className="font-mono text-sm tabular-nums text-text-faint">{record.date}</span> : null}
        {exercise ? (
          <Link to={`/exercises/${exercise.id}`} className="font-medium text-text hover:text-brand hover:underline">
            {exercise.display_name}
          </Link>
        ) : (
          <span className="font-medium text-text-muted">未指定練習</span>
        )}
        {drillName ? <span className="text-sm text-text-muted">{drillName}</span> : null}
        {record.kind !== DEFAULT_RECORD_KIND ? (
          <Chip tone={record.kind === TEST_KIND ? 'brand' : 'neutral'}>{recordKindLabel(record.kind)}</Chip>
        ) : null}
        {target ? <span className="text-sm text-text-muted">{target}</span> : null}
        <span className="ml-auto flex items-center gap-2">
          {recordHasDuration(record) ? (
            <span className="text-sm tabular-nums text-text-muted">{minutesLabel(recordMinutes(record))}</span>
          ) : null}
          <LinkButton
            to={`/records/${record.id}/edit`}
            size="sm"
            kind="ghost"
            aria-label={`編輯 ${record.date} 的紀錄`}
          >
            編輯
          </LinkButton>
        </span>
      </div>
      {recordOptions(record).length ? (
        <div className="flex flex-wrap gap-1">
          {recordOptions(record).map((option) => (
            <Chip key={option.id} title={option.description || undefined}>
              {option.value}
            </Chip>
          ))}
        </div>
      ) : null}
      {notes ? <p className="whitespace-pre-line text-sm leading-relaxed text-text">{notes}</p> : null}
      {references.length ? (
        <ul className="flex flex-wrap gap-x-3 text-sm">
          {references.map((reference) => (
            <li key={reference.id ?? reference.url}>
              {isWebLink(reference.url) ? (
                <a href={reference.url} target="_blank" rel="noopener noreferrer" className="text-brand hover:underline">
                  {reference.name || reference.url} ↗
                </a>
              ) : (
                <span className="text-text-muted">{reference.name || reference.url}</span>
              )}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}

export default function RecordList({ records, label, showDate = true }) {
  return (
    <ul className="space-y-2" aria-label={label}>
      {records.map((record) => (
        <li key={record.id}>
          <RecordRow record={record} showDate={showDate} />
        </li>
      ))}
    </ul>
  )
}
