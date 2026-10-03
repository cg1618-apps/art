// Frontend: the drill library, /drills.
//
// ExerciseLibrary's shape: the search box and two filters in the URL
// (hooks/useUrlFilters), applied by the server - `q` over the drill's name and
// instructions and its exercise's names and aliases, `topic_id` one of the
// exercise's topics, `source_id` one source. The list is grouped by the
// exercise's stage in roadmap order, then 不分階段 (lib/exercises.js); inside a
// group the server's order is kept, which is by exercise and then by the
// drill's position in it.
//
// Each card is the drill's name, its exercise's name, its source, the round,
// the suggested minutes and the frequency, and two numbers: how many records
// name the drill and how many minutes they add up to.
import { keepPreviousData } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { endpoints } from '../../api/endpoints'
import { FilterGroup, FilterOptions } from '../../components/layout/FilterPanel'
import LibraryLayout from '../../components/layout/LibraryLayout'
import { Chip, Section } from '../../components/ui/primitives'
import { useApiQuery, useOptions } from '../../hooks/useApi'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import { drillAmount, groupByStage, minutesLabel } from '../../lib/exercises'

const SPEC = {
  topic: { type: 'single', api: 'topic_id', id: true },
  source: { type: 'single', api: 'source_id', id: true },
}

function filterOptions(options) {
  return (options ?? []).map((option) => ({
    value: String(option.id),
    label: option.value,
    title: option.description,
  }))
}

function DrillCard({ drill }) {
  const facts = [drillAmount(drill), minutesLabel(drill.suggested_minutes), drill.frequency].filter(Boolean)
  return (
    <Link
      to={`/drills/${drill.id}`}
      className="group block h-full space-y-2 rounded-lg border border-border bg-surface p-4 transition-colors hover:border-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
    >
      <div className="space-y-0.5">
        <p className="font-display text-lg font-bold leading-snug text-text group-hover:text-brand">
          {drill.display_name}
        </p>
        <p className="text-xs text-text-muted">{drill.exercise.display_name}</p>
      </div>
      {drill.source ? (
        <div className="flex flex-wrap gap-1">
          <Chip tone="brand" title={drill.source.description || undefined}>
            {drill.source.value}
          </Chip>
        </div>
      ) : null}
      {facts.length ? <p className="text-sm tabular-nums text-text-muted">{facts.join(' · ')}</p> : null}
      <p className="text-xs tabular-nums text-text-faint">
        {drill.record_count ?? 0} 筆紀錄 · {drill.total_minutes ?? 0} 分鐘
      </p>
    </Link>
  )
}

function GroupedList({ drills }) {
  return (
    <div className="space-y-6">
      {groupByStage(drills).map((group) => (
        <Section key={group.key} title={group.title}>
          <ul className="grid gap-3 sm:grid-cols-2" aria-label={group.title}>
            {group.items.map((drill) => (
              <li key={drill.id}>
                <DrillCard drill={drill} />
              </li>
            ))}
          </ul>
        </Section>
      ))}
    </div>
  )
}

export default function DrillLibrary() {
  const filters = useUrlFilters(SPEC)
  const drills = useApiQuery(endpoints.drills.list(), filters.apiParams, {
    placeholderData: keepPreviousData,
  })
  const topics = useOptions('topic')
  const sources = useOptions('source')

  const sidebar = (
    <>
      <FilterGroup title="主題">
        <FilterOptions
          options={filterOptions(topics.data)}
          selected={filters.values.topic}
          onToggle={(value) => filters.toggle('topic', value)}
        />
      </FilterGroup>
      <FilterGroup title="來源">
        <FilterOptions
          options={filterOptions(sources.data)}
          selected={filters.values.source}
          onToggle={(value) => filters.toggle('source', value)}
        />
      </FilterGroup>
    </>
  )

  return (
    <LibraryLayout
      title="練法"
      add={{ to: '/drills/new', label: '新增練法' }}
      filters={filters}
      sidebar={sidebar}
      query={drills}
      renderList={(items) => <GroupedList drills={items} />}
      searchPlaceholder="搜尋練法、步驟或練習項目…"
      emptyText="還沒有任何練法。"
      noMatchText="沒有符合條件的練法。"
    />
  )
}
