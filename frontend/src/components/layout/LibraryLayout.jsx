// Frontend: the scaffold every library page shares.
//
// food's LibraryLayout - title bar with the add button, a filter sidebar on a
// desktop and a drawer on a phone, the search box, a result count, then the
// list - without its 封面 / 清單 toggle: nothing in art has a cover yet, so
// the list is one shape, cards, drawn by the page through `renderItem`.
//
// The page supplies its data and its words; this owns the arrangement and the
// three states. Two empties are different directions and say so: an empty
// LIBRARY offers the add button, an empty RESULT offers clearing the filters.
//
// Props:
//   title         - the page heading, e.g. 筆記
//   add           - { to, label } for the add button
//   filters       - the useUrlFilters(spec) result
//   sidebar       - the filter controls (components/layout/FilterPanel)
//   query         - the list's useApiQuery result
//   renderItem    - (item) => the <li>'s content
//   searchPlaceholder, emptyText, noMatchText
import { useState } from 'react'

import Dialog from '../ui/Dialog'
import { Button, Input, LinkButton } from '../ui/primitives'
import { Empty, ErrorNote, Loading } from '../ui/states'

function FilterCount({ count }) {
  if (!count) return null
  return (
    <span className="rounded-full bg-brand px-1.5 text-xs leading-5 tabular-nums text-on-brand">
      {count}
    </span>
  )
}

export default function LibraryLayout({
  title,
  add,
  filters,
  sidebar,
  query,
  renderItem,
  searchPlaceholder = '搜尋…',
  emptyText = '這裡還沒有東西。',
  noMatchText = '沒有符合條件的項目。',
}) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const items = query.data ?? []

  const addButton = add ? (
    <LinkButton kind="primary" to={add.to}>
      {add.label}
    </LinkButton>
  ) : null

  const clearButton = <Button onClick={filters.clearAll}>清除搜尋與篩選</Button>

  let body
  if (query.isPending) body = <Loading />
  else if (query.error) body = <ErrorNote error={query.error} />
  else if (items.length === 0 && filters.isFiltered) body = <Empty action={clearButton}>{noMatchText}</Empty>
  else if (items.length === 0) body = <Empty action={addButton}>{emptyText}</Empty>
  else
    body = (
      <ul className="grid gap-3 sm:grid-cols-2" aria-label={title}>
        {items.map((item) => (
          <li key={item.id}>{renderItem(item)}</li>
        ))}
      </ul>
    )

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-3xl font-bold">{title}</h1>
        {addButton}
      </div>

      <div className="lg:grid lg:grid-cols-[13rem_minmax(0,1fr)] lg:gap-8">
        <aside aria-label="篩選" className="hidden space-y-5 lg:block">
          {sidebar}
          {filters.activeCount ? (
            <Button size="sm" kind="ghost" onClick={filters.clear}>
              清除篩選
            </Button>
          ) : null}
        </aside>

        <div className="min-w-0 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              type="search"
              aria-label="搜尋"
              value={filters.search}
              onChange={(event) => filters.setSearch(event.target.value)}
              placeholder={searchPlaceholder}
              className="min-w-0 flex-1 basis-48"
            />
            <Button
              className="lg:hidden"
              aria-haspopup="dialog"
              aria-expanded={drawerOpen}
              onClick={() => setDrawerOpen(true)}
            >
              篩選
              <FilterCount count={filters.activeCount} />
            </Button>
          </div>

          {query.data ? (
            <p className="text-xs text-text-faint" aria-live="polite">
              共 {items.length} 筆
            </p>
          ) : null}

          {body}
        </div>
      </div>

      {drawerOpen ? (
        <Dialog
          title="篩選"
          onClose={() => setDrawerOpen(false)}
          footer={
            <>
              <Button kind="ghost" onClick={filters.clear} disabled={!filters.activeCount}>
                清除篩選
              </Button>
              <Button kind="primary" onClick={() => setDrawerOpen(false)}>
                看 {items.length} 筆結果
              </Button>
            </>
          }
        >
          <div className="space-y-5">{sidebar}</div>
        </Dialog>
      ) : null}
    </div>
  )
}
