// Frontend: the list operations a sub-row editor shares, and the small field
// helpers every form uses.
//
// food's rowList, with one difference: food reorders by dragging (dnd-kit);
// art's one row list - a note's resources - is short, so a row moves up or
// down by a button and no drag library is needed. The reducer's `move` is the
// same either way.
//
// Each row carries a `_key` that never leaves the browser: React needs a key
// that survives a reorder, and an index is exactly the key that does not. The
// payload builders pick their fields by name, so `_key` is never sent.

let counter = 0

/** A key unique for the life of the page. */
export function nextKey() {
  counter += 1
  return `row-${counter}`
}

/** The row with a `_key`, keeping one it already has. */
export function keyed(row) {
  return row._key ? row : { ...row, _key: nextKey() }
}

/**
 * Apply one action to a list of rows and return the new list. Never mutates.
 *
 *   { type: 'add', row }              append
 *   { type: 'update', index, patch }  merge `patch` into one row
 *   { type: 'remove', index }
 *   { type: 'move', from, to }        take the row at `from` and put it at
 *                                     `to`; an index off either end is a
 *                                     no-op, not a wrap
 */
export function rowsReducer(rows, action) {
  switch (action.type) {
    case 'add':
      return [...rows, keyed(action.row)]
    case 'update':
      return rows.map((row, i) => (i === action.index ? { ...row, ...action.patch } : row))
    case 'remove':
      return rows.filter((_, i) => i !== action.index)
    case 'move': {
      const { from, to } = action
      if (from === to || from < 0 || to < 0 || from >= rows.length || to >= rows.length) return rows
      const next = [...rows]
      const [row] = next.splice(from, 1)
      next.splice(to, 0, row)
      return next
    }
    default:
      throw new Error(`Unknown row action: ${action.type}`)
  }
}

/** '' -> null, and anything else trimmed: an empty field is an absent value. */
export function blankToNull(value) {
  if (value === null || value === undefined) return null
  const text = String(value).trim()
  return text === '' ? null : text
}

/** A number input's string as an integer, or null when it is empty or not a number. */
export function integerOrNull(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? Math.round(n) : null
}

/**
 * Aliases as typed into one box: split on commas (ASCII or Chinese), the
 * enumeration comma and newlines, trimmed, empties dropped. The server refuses
 * a duplicate, so a case-insensitive repeat is dropped here rather than sent
 * to fail.
 */
export function splitAliases(text) {
  const seen = new Set()
  const out = []
  for (const part of String(text ?? '').split(/[,，、\n]/)) {
    const value = part.trim()
    if (!value || seen.has(value.toLowerCase())) continue
    seen.add(value.toLowerCase())
    out.push(value)
  }
  return out
}
