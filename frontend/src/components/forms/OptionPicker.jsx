// Frontend: choose one option, or any number of them, from one category.
//
// Every field that picks a system option goes through this, because the spec
// asks the same two things of all of them: the value's DESCRIPTION is shown
// where it is picked (as the chip's tooltip, and in a line under the chips for
// the one in focus or chosen), and a small link goes to /options, where the
// vocabulary is changed.
//
// Toggle chips, as food's ChipPicker - buttons with aria-pressed. `multiple`
// false makes it a single choice that clicking again clears, the shape a
// nullable field like a note's category has.
//
//   options   [Option] - { id, value, description } as GET /api/options serves
//   value     an id or null (single), or [ids] (multiple)
//   onChange  (next) => void
//   multiple  any number (true) or one (false)
//   label     the group's accessible name
//   empty     shown when the category has no values yet
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { cx } from '../../lib/cx'
import { FOCUS_RING } from '../ui/primitives'

export default function OptionPicker({
  options,
  value,
  onChange,
  multiple = false,
  label,
  empty = '這個分類還沒有選項。',
}) {
  const [hovered, setHovered] = useState(null)
  const chosen = new Set(multiple ? value : value == null ? [] : [value])

  function toggle(id) {
    if (multiple) onChange(chosen.has(id) ? value.filter((v) => v !== id) : [...value, id])
    else onChange(chosen.has(id) ? null : id)
  }

  // The description shown under the chips: the one pointed at, else the one
  // chosen when there is exactly one.
  const described =
    (options ?? []).find((option) => option.id === hovered) ??
    (chosen.size === 1 ? (options ?? []).find((option) => chosen.has(option.id)) : null)

  return (
    <div className="space-y-1.5">
      {options?.length ? (
        <div role="group" aria-label={label} className="flex flex-wrap gap-1.5">
          {options.map((option) => {
            const pressed = chosen.has(option.id)
            return (
              <button
                key={option.id}
                type="button"
                aria-pressed={pressed}
                title={option.description || undefined}
                onClick={() => toggle(option.id)}
                onMouseEnter={() => setHovered(option.id)}
                onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered(option.id)}
                onBlur={() => setHovered(null)}
                className={cx(
                  'rounded-full border px-2.5 py-0.5 text-sm transition-colors',
                  FOCUS_RING,
                  pressed
                    ? 'border-brand/40 bg-brand-soft text-brand'
                    : 'border-border bg-surface text-text-muted hover:border-border-strong hover:text-text',
                )}
              >
                {option.value}
              </button>
            )
          })}
        </div>
      ) : (
        <p className="text-sm text-text-faint">{empty}</p>
      )}
      <p className="flex flex-wrap items-baseline justify-between gap-2 text-xs">
        <span className="min-h-4 text-text-muted">{described?.description ?? ''}</span>
        <Link to="/options" className="text-text-faint hover:text-brand hover:underline">
          管理選項
        </Link>
      </p>
    </div>
  )
}
