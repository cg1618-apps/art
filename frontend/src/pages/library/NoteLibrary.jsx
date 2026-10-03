// Frontend: the notes library, /notes.
//
// The search box and two filters, category and topic, all in the URL
// (hooks/useUrlFilters) and all applied by the server: `q` over the names,
// the aliases and the summary; repeated `category_id` and `topic_id`, each
// "any of". The server orders by display name.
//
// Each card is the note's name, its category, its topics and its summary - the
// summary is what a 名詞 is defined by, so it is what a scan of the list reads.
import { keepPreviousData } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { endpoints } from '../../api/endpoints'
import { FilterGroup, FilterOptions } from '../../components/layout/FilterPanel'
import LibraryLayout from '../../components/layout/LibraryLayout'
import { Chip } from '../../components/ui/primitives'
import { useApiQuery, useOptions } from '../../hooks/useApi'
import { useUrlFilters } from '../../hooks/useUrlFilters'

const SPEC = {
  category: { type: 'multi', api: 'category_id', id: true },
  topic: { type: 'multi', api: 'topic_id', id: true },
}

function filterOptions(options) {
  return (options ?? []).map((option) => ({
    value: String(option.id),
    label: option.value,
    title: option.description,
  }))
}

function NoteCard({ note }) {
  return (
    <Link
      to={`/notes/${note.id}`}
      className="group block h-full space-y-2 rounded-lg border border-border bg-surface p-4 transition-colors hover:border-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 font-display text-lg font-bold leading-snug text-text group-hover:text-brand">
          {note.display_name}
        </p>
        {note.category ? (
          <Chip tone="brand" className="shrink-0" title={note.category.description || undefined}>
            {note.category.value}
          </Chip>
        ) : null}
      </div>
      {note.summary ? <p className="line-clamp-3 text-sm text-text-muted">{note.summary}</p> : null}
      {note.topics?.length ? (
        <div className="flex flex-wrap gap-1">
          {note.topics.map((topic) => (
            <Chip key={topic.id} title={topic.description || undefined}>
              {topic.value}
            </Chip>
          ))}
        </div>
      ) : null}
    </Link>
  )
}

export default function NoteLibrary() {
  const filters = useUrlFilters(SPEC)
  const { values, toggle } = filters

  const notes = useApiQuery(endpoints.notes.list(), filters.apiParams, {
    placeholderData: keepPreviousData,
  })
  const categories = useOptions('note_category')
  const topics = useOptions('topic')

  const sidebar = (
    <>
      <FilterGroup title="分類">
        <FilterOptions
          options={filterOptions(categories.data)}
          selected={values.category}
          onToggle={(value) => toggle('category', value)}
        />
      </FilterGroup>
      <FilterGroup title="主題">
        <FilterOptions
          options={filterOptions(topics.data)}
          selected={values.topic}
          onToggle={(value) => toggle('topic', value)}
        />
      </FilterGroup>
    </>
  )

  return (
    <LibraryLayout
      title="筆記"
      add={{ to: '/notes/new', label: '新增筆記' }}
      filters={filters}
      sidebar={sidebar}
      query={notes}
      renderItem={(note) => <NoteCard note={note} />}
      searchPlaceholder="搜尋名稱、別名或摘要…"
      emptyText="還沒有任何筆記。"
      noMatchText="沒有符合條件的筆記。"
    />
  )
}
