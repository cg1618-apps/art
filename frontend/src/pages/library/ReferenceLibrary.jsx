// Frontend: the references library, /references.
//
// NoteLibrary's shape: the search box and the filters, all in the URL
// (hooks/useUrlFilters) and all applied by the server - `q` over the name,
// the link and the notes; repeated `group_id`, "any of"; and 未分組, the
// references in no group. The server orders by name.
//
// A card is not one link, as a note's is, because it holds two: the name
// opens the reference itself in a new tab - the reason the reference was kept
// - and 詳細 opens its page here, with the notes in full. Under the name, the
// host the link points at, the group chips and the start of the notes.
import { keepPreviousData } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { endpoints } from '../../api/endpoints'
import { FilterGroup, FilterOptions } from '../../components/layout/FilterPanel'
import LibraryLayout from '../../components/layout/LibraryLayout'
import { Chip } from '../../components/ui/primitives'
import { useApiQuery, useOptions } from '../../hooks/useApi'
import { useUrlFilters } from '../../hooks/useUrlFilters'
import { hostOf, isWebLink } from '../../lib/links'

const SPEC = {
  group: { type: 'multi', api: 'group_id', id: true },
  ungrouped: { type: 'bool', api: 'no_group' },
}

const UNGROUPED = [{ value: '1', label: '未分組' }]

function filterOptions(options) {
  return (options ?? []).map((option) => ({
    value: String(option.id),
    label: option.value,
    title: option.description,
  }))
}

function ReferenceCard({ reference }) {
  const name = (
    <span className="font-display text-lg font-bold leading-snug">{reference.name}</span>
  )
  return (
    <article className="h-full space-y-2 rounded-lg border border-border bg-surface p-4">
      <div className="space-y-0.5">
        {isWebLink(reference.url) ? (
          <a
            href={reference.url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded text-text hover:text-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          >
            {name} <span aria-hidden="true">↗</span>
          </a>
        ) : (
          name
        )}
        <p className="truncate text-xs text-text-muted">{hostOf(reference.url)}</p>
      </div>
      {reference.groups?.length ? (
        <div className="flex flex-wrap gap-1">
          {reference.groups.map((group) => (
            <Chip key={group.id} title={group.description || undefined}>
              {group.value}
            </Chip>
          ))}
        </div>
      ) : null}
      {reference.notes_excerpt ? (
        <p className="line-clamp-2 text-sm text-text-muted">{reference.notes_excerpt}</p>
      ) : null}
      <Link
        to={`/references/${reference.id}`}
        aria-label={`${reference.name} 的詳細`}
        className="inline-block rounded text-xs text-brand hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
      >
        詳細
      </Link>
    </article>
  )
}

export default function ReferenceLibrary() {
  const filters = useUrlFilters(SPEC)
  const { values, toggle } = filters

  const references = useApiQuery(endpoints.references.list(), filters.apiParams, {
    placeholderData: keepPreviousData,
  })
  const groups = useOptions('reference_group')

  const sidebar = (
    <FilterGroup title="參考分組">
      <FilterOptions
        options={filterOptions(groups.data)}
        selected={values.group}
        onToggle={(value) => toggle('group', value)}
      />
      <FilterOptions
        options={UNGROUPED}
        selected={values.ungrouped ? '1' : ''}
        onToggle={() => toggle('ungrouped')}
      />
    </FilterGroup>
  )

  return (
    <LibraryLayout
      title="參考"
      add={{ to: '/references/new', label: '新增參考' }}
      filters={filters}
      sidebar={sidebar}
      query={references}
      renderItem={(reference) => <ReferenceCard reference={reference} />}
      searchPlaceholder="搜尋名稱、連結或筆記…"
      emptyText="還沒有任何參考。"
      noMatchText="沒有符合條件的參考。"
    />
  )
}
