// Frontend: the resources of a thing, edited as name + link rows.
//
// A note's resources and a stage's are the same shape - `food`'s tbd_link:
// a name, a link, an order - so both forms edit them with this. Rows are
// added, removed and moved up or down by a button (lib/rowList.js); each row
// carries a `_key` that never leaves the browser.
//
//   rows      [{ _key, name, url }]
//   onChange  (nextRows) => void
//
// lib/rowList.js holds the two conversions every such form owes:
// `resourcesFromApi` and `resourcesToPayload`.
import { rowsReducer } from '../../lib/rowList'
import { Button, Input } from '../ui/primitives'

export default function ResourceRows({ rows, onChange }) {
  const dispatch = (action) => onChange(rowsReducer(rows, action))
  return (
    <div className="space-y-2">
      {rows.length === 0 ? <p className="text-sm text-text-faint">還沒有資源。</p> : null}
      {rows.map((row, index) => {
        const number = index + 1
        return (
          <div
            key={row._key}
            role="group"
            aria-label={`資源 ${number}`}
            className="flex flex-wrap items-center gap-2 rounded-md border border-border bg-surface p-2"
          >
            <Input
              aria-label={`資源 ${number} 名稱`}
              placeholder="名稱"
              value={row.name}
              onChange={(event) => dispatch({ type: 'update', index, patch: { name: event.target.value } })}
              className="min-w-0 flex-1 basis-32"
            />
            <Input
              type="url"
              aria-label={`資源 ${number} 連結`}
              placeholder="https://"
              value={row.url}
              onChange={(event) => dispatch({ type: 'update', index, patch: { url: event.target.value } })}
              className="min-w-0 flex-[2] basis-48"
            />
            <div className="flex shrink-0 gap-1">
              <Button
                size="sm"
                kind="ghost"
                aria-label={`上移資源 ${number}`}
                title="上移"
                disabled={index === 0}
                onClick={() => dispatch({ type: 'move', from: index, to: index - 1 })}
              >
                ↑
              </Button>
              <Button
                size="sm"
                kind="ghost"
                aria-label={`下移資源 ${number}`}
                title="下移"
                disabled={index === rows.length - 1}
                onClick={() => dispatch({ type: 'move', from: index, to: index + 1 })}
              >
                ↓
              </Button>
              <Button
                size="sm"
                kind="ghost"
                className="hover:text-danger"
                aria-label={`移除資源 ${number}`}
                title="移除"
                onClick={() => dispatch({ type: 'remove', index })}
              >
                ✕
              </Button>
            </div>
          </div>
        )
      })}
      <Button size="sm" onClick={() => dispatch({ type: 'add', row: { name: '', url: '' } })}>
        ＋ 新增資源
      </Button>
    </div>
  )
}
