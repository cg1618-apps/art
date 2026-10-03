// Frontend: the page frame - navigation and the content column.
//
// food's frame: a top bar on a desktop and a bar fixed to the bottom of the
// screen on a phone, where the thumb reaches. The main column is padded by the
// bar's height (and the phone's safe area) so the bar never covers the last
// line of a page.
//
// The active section is marked with aria-current="page" and styled from that
// attribute, so what a screen reader announces and what the eye sees cannot
// disagree. See lib/nav.js for the match.
//
// The frame is also where the timer lives (components/timer/): TimerProvider
// is around every page, and while a timer exists its chip sits at the right
// of the top bar. On a phone the top bar holds only the chip, and shows only
// while there is one - the sections are in the bar at the bottom.
import { Link, Outlet, useLocation } from 'react-router-dom'

import { useTimer } from '../../hooks/useTimer'
import { cx } from '../../lib/cx'
import { activeSection, SECTIONS } from '../../lib/nav'
import TimerChip from '../timer/TimerChip'
import TimerProvider from '../timer/TimerProvider'

function NavItems({ active, className }) {
  return SECTIONS.map((section) => (
    <Link
      key={section.key}
      to={section.to}
      aria-current={active === section.key ? 'page' : undefined}
      className={className}
    >
      {section.label}
    </Link>
  ))
}

export default function Layout() {
  return (
    <TimerProvider>
      <Frame />
    </TimerProvider>
  )
}

function Frame() {
  const { pathname } = useLocation()
  const active = activeSection(pathname)
  const { timer } = useTimer()

  return (
    <div className="min-h-screen">
      <header
        className={cx(
          'sticky top-0 z-30 border-b border-border bg-canvas/95 backdrop-blur md:block',
          timer ? 'block' : 'hidden',
        )}
      >
        <div className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-2 md:px-6 md:py-3">
          <nav aria-label="主要" className="flex items-center gap-8">
            <Link
              to="/"
              className="font-display text-2xl font-bold leading-none text-brand"
              aria-label="首頁"
            >
              畫
            </Link>
            <div className="hidden items-center gap-1 md:flex">
              <NavItems
                active={active}
                className="rounded-md px-3 py-1.5 font-display text-[0.95rem] text-text-muted transition-colors hover:text-text aria-[current=page]:bg-brand-soft aria-[current=page]:text-brand"
              />
            </div>
          </nav>
          <div className="ml-auto">
            <TimerChip />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 pt-5 pb-[calc(4.5rem+env(safe-area-inset-bottom))] md:px-6 md:pt-8 md:pb-12">
        <Outlet />
      </main>

      <nav
        aria-label="主要"
        style={{ gridTemplateColumns: `repeat(${SECTIONS.length}, minmax(0, 1fr))` }}
        className="fixed inset-x-0 bottom-0 z-30 grid border-t border-border bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
      >
        <NavItems
          active={active}
          className="relative truncate px-1 py-3 text-center font-display text-base text-text-muted aria-[current=page]:text-brand aria-[current=page]:before:absolute aria-[current=page]:before:inset-x-4 aria-[current=page]:before:top-0 aria-[current=page]:before:h-0.5 aria-[current=page]:before:rounded-full aria-[current=page]:before:bg-brand"
        />
      </nav>
    </div>
  )
}
