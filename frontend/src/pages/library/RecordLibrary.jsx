// Frontend: the practice log, /records.
//
// LibraryLayout without its search box - the record list is not searched -
// and with two filters in the URL (hooks/useUrlFilters), applied by the
// server: the kind, and the exercise (records naming it directly or through
// one of its drills).
//
// The records are grouped by date, newest first, each day under its total
// minutes - summed from the records shown, so a filtered day totals what is
// filtered. Above the list, this week's total (Monday to Sunday, the
// browser's dates) from GET /api/records/summary, which is every record's
// whatever the filters. A record with no duration counts as zero minutes.
import { keepPreviousData } from '@tanstack/react-query'

import { endpoints } from '../../api/endpoints'
import RecordList from '../../components/RecordList'
import { FilterGroup, FilterOptions } from '../../components/layout/FilterPanel'
import LibraryLayout from '../../components/layout/LibraryLayout'
import { Section, Select } from '../../components/ui/primitives'
import { useApiQuery } from '../../hooks/useApi'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import { minutesLabel } from '../../lib/exercises'
import { groupByDate, RECORD_KINDS, summaryMinutes, weekdayLabel, weekRange } from '../../lib/records'

const SPEC = {
  kind: { type: 'single', api: 'kind' },
  exercise: { type: 'single', api: 'exercise_id', id: true },
}

const KIND_OPTIONS = RECORD_KINDS.map((kind) => ({ value: kind.value, label: kind.label }))

function DayList({ records }) {
  return (
    <div className="space-y-6">
      {groupByDate(records).map((day) => (
        <Section
          key={day.date}
          title={`${day.date}（${weekdayLabel(day.date)}）`}
          actions={
            <span className="text-sm tabular-nums text-text-muted">共 {minutesLabel(day.minutes)}</span>
          }
        >
          <RecordList records={day.records} label={day.date} showDate={false} />
        </Section>
      ))}
    </div>
  )
}

function WeekTotal() {
  const week = weekRange()
  const summary = useApiQuery(endpoints.records.summary(), week)
  if (!summary.data) return null
  return (
    <p className="text-sm text-text-muted">
      本週（{week.from} – {week.to}）共{' '}
      <span className="font-bold tabular-nums text-text" data-testid="week-minutes">
        {summaryMinutes(summary.data)}
      </span>{' '}
      分鐘
    </p>
  )
}

export default function RecordLibrary() {
  const filters = useUrlFilters(SPEC)
  const records = useApiQuery(endpoints.records.list(), filters.apiParams, {
    placeholderData: keepPreviousData,
  })
  const exercises = useApiQuery(endpoints.exercises.list())

  const sidebar = (
    <>
      <FilterGroup title="類型">
        <FilterOptions
          options={KIND_OPTIONS}
          selected={filters.values.kind}
          onToggle={(value) => filters.toggle('kind', value)}
        />
      </FilterGroup>
      <FilterGroup title="練習項目">
        <Select
          aria-label="練習項目"
          value={filters.values.exercise}
          onChange={(event) => filters.setValue('exercise', event.target.value)}
        >
          <option value="">全部</option>
          {(exercises.data ?? []).map((exercise) => (
            <option key={exercise.id} value={String(exercise.id)}>
              {exercise.display_name}
            </option>
          ))}
        </Select>
      </FilterGroup>
    </>
  )

  return (
    <LibraryLayout
      title="紀錄"
      add={{ to: '/records/new', label: '新增紀錄' }}
      filters={filters}
      sidebar={sidebar}
      query={records}
      searchable={false}
      renderList={(items) => (
        <div className="space-y-4">
          <WeekTotal />
          <DayList records={items} />
        </div>
      )}
      emptyText="還沒有任何紀錄。"
      noMatchText="沒有符合條件的紀錄。"
    />
  )
}
