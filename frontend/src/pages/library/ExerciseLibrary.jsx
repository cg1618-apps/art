// Frontend: the exercise library, /exercises.
//
// NoteLibrary's shape: the search box and a topic filter in the URL
// (hooks/useUrlFilters), applied by the server - `q` over the names and
// aliases, `topic_id` one topic. The list is grouped by stage in roadmap
// order, then 不分階段 for the exercises practised at every level
// (lib/exercises.js).
//
// Each card is the exercise's name, its description, its topics, and three
// numbers: how many drills, how many records, how many minutes in all.
import { keepPreviousData } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { endpoints } from '../../api/endpoints'
import { FilterGroup, FilterOptions } from '../../components/layout/FilterPanel'
import LibraryLayout from '../../components/layout/LibraryLayout'
import { Chip, Section } from '../../components/ui/primitives'
import { useApiQuery, useOptions } from '../../hooks/useApi'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import { groupByStage } from '../../lib/exercises'

const SPEC = {
  topic: { type: 'single', api: 'topic_id', id: true },
}

function filterOptions(options) {
  return (options ?? []).map((option) => ({
    value: String(option.id),
    label: option.value,
    title: option.description,
  }))
}

function ExerciseCard({ exercise }) {
  return (
    <Link
      to={`/exercises/${exercise.id}`}
      className="group block h-full space-y-2 rounded-lg border border-border bg-surface p-4 transition-colors hover:border-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
    >
      <p className="font-display text-lg font-bold leading-snug text-text group-hover:text-brand">
        {exercise.display_name}
      </p>
      {exercise.description ? <p className="line-clamp-3 text-sm text-text-muted">{exercise.description}</p> : null}
      {exercise.topics?.length ? (
        <div className="flex flex-wrap gap-1">
          {exercise.topics.map((topic) => (
            <Chip key={topic.id} title={topic.description || undefined}>
              {topic.value}
            </Chip>
          ))}
        </div>
      ) : null}
      <p className="text-xs tabular-nums text-text-faint">
        {exercise.drill_count ?? 0} 個練法 · {exercise.record_count ?? 0} 筆紀錄 · {exercise.total_minutes ?? 0} 分鐘
      </p>
    </Link>
  )
}

function GroupedList({ exercises }) {
  return (
    <div className="space-y-6">
      {groupByStage(exercises).map((group) => (
        <Section key={group.key} title={group.title}>
          <ul className="grid gap-3 sm:grid-cols-2" aria-label={group.title}>
            {group.items.map((exercise) => (
              <li key={exercise.id}>
                <ExerciseCard exercise={exercise} />
              </li>
            ))}
          </ul>
        </Section>
      ))}
    </div>
  )
}

export default function ExerciseLibrary() {
  const filters = useUrlFilters(SPEC)
  const exercises = useApiQuery(endpoints.exercises.list(), filters.apiParams, {
    placeholderData: keepPreviousData,
  })
  const topics = useOptions('topic')

  const sidebar = (
    <FilterGroup title="主題">
      <FilterOptions
        options={filterOptions(topics.data)}
        selected={filters.values.topic}
        onToggle={(value) => filters.toggle('topic', value)}
      />
    </FilterGroup>
  )

  return (
    <LibraryLayout
      title="練習"
      add={{ to: '/exercises/new', label: '新增練習項目' }}
      filters={filters}
      sidebar={sidebar}
      query={exercises}
      renderList={(items) => <GroupedList exercises={items} />}
      searchPlaceholder="搜尋名稱或別名…"
      emptyText="還沒有任何練習項目。"
      noMatchText="沒有符合條件的練習項目。"
    />
  )
}
