// Frontend: the design primitives.
//
// food's, copied so the two apps look like one product; only the ones art uses
// so far are here, and a later module copies the next one from food rather
// than inventing its own.
//
// Two rules hold for every component in this file:
//   - every colour is a semantic token (index.css, theme-tokens.test.js);
//   - `className` EXTENDS the base classes, it never replaces them. A layout
//     class like `sm:col-span-2` passed to an Input must not cost it its
//     border.
import { Link } from 'react-router-dom'

import { cx } from '../../lib/cx'

export const FOCUS_RING =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-1 focus-visible:ring-offset-canvas'

// Four kinds, media's set. `primary` is the one action a screen is for;
// `outline` everything else; `danger` destroys; `ghost` sits inside a row.
const BUTTON_KINDS = {
  primary: 'border border-brand bg-brand text-on-brand hover:border-brand-hover hover:bg-brand-hover',
  outline: 'border border-border-strong bg-surface text-text hover:border-text',
  danger: 'border border-danger bg-surface text-danger hover:bg-danger hover:text-on-brand',
  ghost: 'border border-transparent text-text-muted hover:bg-surface-2 hover:text-text',
}

const BUTTON_SIZES = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3.5 py-1.5 text-sm',
}

export function Button({ kind = 'outline', size = 'md', type = 'button', className, ...rest }) {
  return (
    <button
      type={type}
      className={cx(
        'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50',
        FOCUS_RING,
        BUTTON_SIZES[size] || BUTTON_SIZES.md,
        BUTTON_KINDS[kind] || BUTTON_KINDS.outline,
        className,
      )}
      {...rest}
    />
  )
}

// A link that looks like a Button. "Add a note" navigates rather than
// submits, so it is an <a>: it opens in a new tab like any other link.
export function LinkButton({ kind = 'outline', size = 'md', className, ...rest }) {
  return (
    <Link
      className={cx(
        'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors',
        FOCUS_RING,
        BUTTON_SIZES[size] || BUTTON_SIZES.md,
        BUTTON_KINDS[kind] || BUTTON_KINDS.outline,
        className,
      )}
      {...rest}
    />
  )
}

// A label over a control, with an optional hint under it. A <label> wraps the
// control so clicking the words focuses it without an id to keep in step.
export function Field({ label, hint, className, children }) {
  return (
    // min-w-0: as a grid or flex item a Field would otherwise refuse to shrink
    // below its input's intrinsic width and run out of its column.
    <label className={cx('block min-w-0 space-y-1', className)}>
      <span className="text-sm font-medium text-text-muted">{label}</span>
      {children}
      {hint ? <span className="block text-xs text-text-faint">{hint}</span> : null}
    </label>
  )
}

const CONTROL =
  'w-full rounded-md border border-border-strong bg-surface px-2.5 py-1.5 text-sm text-text placeholder:text-text-faint disabled:opacity-60'

export function Input({ className, ...rest }) {
  return <input className={cx(CONTROL, FOCUS_RING, className)} {...rest} />
}

export function TextArea({ className, rows = 4, ...rest }) {
  return (
    <textarea rows={rows} className={cx(CONTROL, FOCUS_RING, 'leading-relaxed', className)} {...rest} />
  )
}

export function Select({ className, children, ...rest }) {
  return (
    <select className={cx(CONTROL, FOCUS_RING, 'pr-8', className)} {...rest}>
      {children}
    </select>
  )
}

// A bordered panel, for a block that has to read as one object.
export function Card({ className, ...rest }) {
  return <div className={cx('rounded-lg border border-border bg-surface p-4', className)} {...rest} />
}

// A small rounded tag. Colour does not encode a category: every chip is ink,
// except `brand` for the one the page points at, `warn` for work still owed,
// `ok` for done, `danger` for the destructive.
const CHIP_TONES = {
  neutral: 'border-border bg-surface-2 text-text-muted',
  brand: 'border-brand/40 bg-brand-soft text-brand',
  warn: 'border-warn/40 bg-warn-soft text-warn',
  ok: 'border-ok/40 bg-surface text-ok',
  danger: 'border-danger/40 bg-surface text-danger',
}

export function Chip({ tone = 'neutral', className, children, ...rest }) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs leading-tight',
        CHIP_TONES[tone] || CHIP_TONES.neutral,
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  )
}

// A titled block in a single reading column: a serif heading on a ruled line,
// the way a notebook page is divided. `actions` sits at the right end of the
// rule. The heading level is a prop because a section under a page's h1 is an
// h2, and one inside a dialog may be an h3.
export function Section({ title, actions, as: Heading = 'h2', className, children, ...rest }) {
  return (
    <section className={cx('space-y-3', className)} {...rest}>
      {title || actions ? (
        <div className="flex items-baseline gap-3">
          {title ? (
            <Heading className="shrink-0 text-lg font-bold text-text">{title}</Heading>
          ) : null}
          <span aria-hidden="true" className="flex-1 translate-y-[-0.2em] border-t border-border" />
          {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  )
}
