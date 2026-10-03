// Frontend: the system options, /options.
//
// One section per category the code registers (GET /api/options/categories),
// in the registry's order: the category's label, its description - what the
// category is for, said before its values - then a table of its values with
// what each means (description), a note to yourself (remark), its order and
// how many notes use it. Add, edit and delete happen in place.
//
// A delete states its count before it happens and sends that count back as
// ?in_use=<n>; the server recounts and refuses with a 409 when the number
// moved. The dialog then shows the server's sentence and the corrected count,
// the list is refetched, and the button is offered again - no reload.
//
// Every option is read in one request and grouped here, rather than one
// request per category: there are a handful of categories and a few dozen
// values, and one read keeps the in_use counts consistent with each other.
import { useState } from 'react'

import { buildUrl } from '../../api/client'
import { endpoints } from '../../api/endpoints'
import DeleteDialog from '../../components/forms/DeleteDialog'
import { Button, Input, Section } from '../../components/ui/primitives'
import { Empty, ErrorNote, Loading } from '../../components/ui/states'
import { useApiMutation, useApiQuery, useOptionCategories } from '../../hooks/useApi'
import { blankToNull, integerOrNull } from '../../lib/rowList'

// An option change moves what every note shows.
const INVALIDATE = [endpoints.options.list(), endpoints.notes.list()]

const CELL = 'px-2 py-1.5 align-top'

/** The sort_order a new value gets when none is typed: after the last one. */
function nextSortOrder(rows) {
  return rows.length ? Math.max(...rows.map((row) => row.sort_order ?? 0)) + 1 : 0
}

function draftOf(option) {
  return {
    value: option?.value ?? '',
    description: option?.description ?? '',
    remark: option?.remark ?? '',
    sort_order: option ? String(option.sort_order ?? 0) : '',
  }
}

// The four editable cells, shared by the edit row and the add row.
function DraftCells({ draft, setDraft, name }) {
  const set = (field) => (event) => setDraft({ ...draft, [field]: event.target.value })
  return (
    <>
      <td className={CELL}>
        <Input aria-label={`${name} 值`} value={draft.value} onChange={set('value')} required autoFocus />
      </td>
      <td className={CELL}>
        <Input aria-label={`${name} 說明`} value={draft.description} onChange={set('description')} />
      </td>
      <td className={CELL}>
        <Input aria-label={`${name} 備註`} value={draft.remark} onChange={set('remark')} />
      </td>
      <td className={CELL}>
        <Input
          type="number"
          step="1"
          aria-label={`${name} 順序`}
          value={draft.sort_order}
          onChange={set('sort_order')}
          className="w-20"
        />
      </td>
    </>
  )
}

function OptionRow({ option, onSave, onDelete }) {
  const [draft, setDraft] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function save() {
    setBusy(true)
    setError(null)
    try {
      await onSave({
        value: draft.value.trim(),
        description: blankToNull(draft.description),
        remark: blankToNull(draft.remark),
        sort_order: integerOrNull(draft.sort_order) ?? 0,
      })
      setDraft(null)
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  if (draft) {
    return (
      <>
        <tr
          className="border-t border-border bg-surface-2"
          onKeyDown={(event) => {
            if (event.key === 'Escape') setDraft(null)
            if (event.key === 'Enter') {
              event.preventDefault()
              save()
            }
          }}
        >
          <DraftCells draft={draft} setDraft={setDraft} name={`「${option.value}」的`} />
          <td className={`${CELL} tabular-nums text-text-muted`}>{option.in_use}</td>
          <td className={`${CELL} whitespace-nowrap text-right`}>
            <Button size="sm" kind="primary" onClick={save} disabled={busy || !draft.value.trim()}>
              儲存
            </Button>{' '}
            <Button size="sm" onClick={() => setDraft(null)} disabled={busy}>
              取消
            </Button>
          </td>
        </tr>
        {error ? (
          <tr>
            <td colSpan={6} className={CELL}>
              <ErrorNote error={error} />
            </td>
          </tr>
        ) : null}
      </>
    )
  }

  return (
    <tr className="border-t border-border">
      <td className={`${CELL} font-medium text-text`}>{option.value}</td>
      <td className={`${CELL} text-text-muted`}>{option.description}</td>
      <td className={`${CELL} text-text-faint`}>{option.remark}</td>
      <td className={`${CELL} tabular-nums text-text-muted`}>{option.sort_order}</td>
      <td className={`${CELL} tabular-nums text-text-muted`}>{option.in_use}</td>
      <td className={`${CELL} whitespace-nowrap text-right`}>
        <Button size="sm" kind="ghost" onClick={() => setDraft(draftOf(option))} aria-label={`編輯「${option.value}」`}>
          編輯
        </Button>
        <Button
          size="sm"
          kind="ghost"
          className="hover:text-danger"
          onClick={onDelete}
          aria-label={`刪除「${option.value}」`}
        >
          刪除
        </Button>
      </td>
    </tr>
  )
}

function AddRow({ category, rows, onAdd }) {
  const [draft, setDraft] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function add() {
    setBusy(true)
    setError(null)
    try {
      await onAdd({
        category: category.key,
        value: draft.value.trim(),
        description: blankToNull(draft.description),
        remark: blankToNull(draft.remark),
        sort_order: integerOrNull(draft.sort_order) ?? nextSortOrder(rows),
      })
      setDraft(null)
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  if (!draft) {
    return (
      <tr className="border-t border-border">
        <td colSpan={6} className={CELL}>
          <Button size="sm" onClick={() => setDraft(draftOf(null))}>
            ＋ 新增{category.label}
          </Button>
        </td>
      </tr>
    )
  }

  return (
    <>
      <tr
        className="border-t border-border bg-surface-2"
        onKeyDown={(event) => {
          if (event.key === 'Escape') setDraft(null)
          if (event.key === 'Enter') {
            event.preventDefault()
            if (draft.value.trim()) add()
          }
        }}
      >
        <DraftCells draft={draft} setDraft={setDraft} name={`新${category.label}的`} />
        <td className={CELL} />
        <td className={`${CELL} whitespace-nowrap text-right`}>
          <Button size="sm" kind="primary" onClick={add} disabled={busy || !draft.value.trim()}>
            新增
          </Button>{' '}
          <Button size="sm" onClick={() => setDraft(null)} disabled={busy}>
            取消
          </Button>
        </td>
      </tr>
      {error ? (
        <tr>
          <td colSpan={6} className={CELL}>
            <ErrorNote error={error} />
          </td>
        </tr>
      ) : null}
    </>
  )
}

function CategorySection({ category, rows, create, update, onDelete }) {
  return (
    <Section title={category.label} aria-label={category.label}>
      {category.description ? <p className="text-sm text-text-muted">{category.description}</p> : null}
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[40rem] text-sm">
          <thead className="text-left text-xs text-text-muted">
            <tr>
              <th className={`${CELL} font-medium`}>值</th>
              <th className={`${CELL} font-medium`}>說明</th>
              <th className={`${CELL} font-medium`}>備註</th>
              <th className={`${CELL} font-medium`}>順序</th>
              <th className={`${CELL} font-medium`}>使用中</th>
              <th className={CELL}>
                <span className="sr-only">動作</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr className="border-t border-border">
                <td colSpan={6} className={`${CELL} text-text-faint`}>
                  還沒有任何{category.label}。
                </td>
              </tr>
            ) : null}
            {rows.map((option) => (
              <OptionRow
                key={option.id}
                option={option}
                onSave={(body) => update.mutateAsync({ url: endpoints.options.update(option.id), body })}
                onDelete={() => onDelete(option)}
              />
            ))}
            <AddRow
              category={category}
              rows={rows}
              onAdd={(body) => create.mutateAsync({ url: endpoints.options.create(), body })}
            />
          </tbody>
        </table>
      </div>
    </Section>
  )
}

export default function Options() {
  const categories = useOptionCategories()
  const options = useApiQuery(endpoints.options.list())
  const create = useApiMutation({ method: 'POST', invalidate: INVALIDATE })
  const update = useApiMutation({ method: 'PATCH', invalidate: INVALIDATE })
  const remove = useApiMutation({ method: 'DELETE', invalidate: INVALIDATE })

  // The option being deleted, and the count the dialog states - the page's,
  // until a 409 corrects it.
  const [deleting, setDeleting] = useState(null)

  const byCategory = (key) =>
    (options.data ?? [])
      .filter((option) => option.category === key)
      .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))

  let body
  if (categories.isPending || options.isPending) body = <Loading />
  else if (categories.error || options.error) body = <ErrorNote error={categories.error ?? options.error} />
  else if (!categories.data.length) body = <Empty>還沒有任何選項分類。</Empty>
  else
    body = categories.data.map((category) => (
      <CategorySection
        key={category.key}
        category={category}
        rows={byCategory(category.key)}
        create={create}
        update={update}
        onDelete={(option) => setDeleting({ option, count: option.in_use ?? 0 })}
      />
    ))

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold">選項</h1>
        <p className="text-sm text-text-muted">
          各個欄位可以選的值。改名會在所有用到它的地方一起改；說明會顯示在挑選的時候。
        </p>
      </header>

      {body}

      {deleting ? (
        <DeleteDialog
          title={`刪除選項「${deleting.option.value}」？`}
          onClose={() => setDeleting(null)}
          onConfirm={async () => {
            try {
              await remove.mutateAsync({
                url: buildUrl(endpoints.options.remove(deleting.option.id), { in_use: deleting.count }),
              })
            } catch (caught) {
              // The page's numbers are behind the server's: show them fresh
              // behind the dialog, which keeps the server's sentence.
              if (caught.status === 409) options.refetch()
              throw caught
            }
            setDeleting(null)
          }}
          onStale={(actual) =>
            setDeleting((previous) => (previous ? { ...previous, count: actual } : previous))
          }
        >
          {deleting.count ? (
            <p>
              有 <strong className="tabular-nums">{deleting.count}</strong> 則筆記用到它。刪除後，
              它會從這些筆記拿掉：用作主題的會少一個主題，用作分類的會變成沒有分類。
            </p>
          ) : (
            <p>沒有筆記用到它。刪除後就找不回來了。</p>
          )}
        </DeleteDialog>
      ) : null}
    </div>
  )
}
