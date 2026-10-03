// Frontend: the controls a library's filter sidebar is built from.
//
// food's FilterPanel, the two pieces art uses: a titled group, and toggle chips
// with aria-pressed so a screen reader announces which are on. The sidebar sits
// beside the list on a desktop and in a drawer on a phone (LibraryLayout).
import { cx } from '../../lib/cx'
import { FOCUS_RING } from '../ui/primitives'

/** A titled group of filter controls. `hint` is a line of small print under them. */
export function FilterGroup({ title, hint, children }) {
  return (
    <fieldset className="space-y-2">
      <legend className="mb-2 font-display text-sm font-bold text-text">{title}</legend>
      {children}
      {hint ? <p className="text-xs text-text-faint">{hint}</p> : null}
    </fieldset>
  )
}

function Count({ value }) {
  if (value == null) return null
  return <span className="tabular-nums text-text-faint">{value}</span>
}

function OptionChip({ pressed, onClick, title, children }) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      title={title || undefined}
      className={cx(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs transition-colors',
        FOCUS_RING,
        pressed
          ? 'border-brand bg-brand-soft text-brand'
          : 'border-border-strong bg-surface text-text-muted hover:border-text hover:text-text',
      )}
    >
      {children}
    </button>
  )
}

/**
 * Chips for one filter. `options` is [{ value, label, count?, title? }] with
 * string values (the URL's); `selected` is a string for a single-valued filter
 * or an array for an "any of" one; `onToggle(value)` flips one.
 */
export function FilterOptions({ options, selected, onToggle, empty = '還沒有可選的值' }) {
  if (!options?.length) return <p className="text-xs text-text-faint">{empty}</p>
  const isOn = (value) => (Array.isArray(selected) ? selected.includes(value) : selected === value)
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((option) => (
        <OptionChip
          key={option.value}
          pressed={isOn(option.value)}
          onClick={() => onToggle(option.value)}
          title={option.title}
        >
          {option.label}
          <Count value={option.count} />
        </OptionChip>
      ))}
    </div>
  )
}
