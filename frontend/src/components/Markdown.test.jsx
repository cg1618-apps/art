// A note body is Markdown that may one day be read by people who did not write
// it, so what matters is that links work, leave the site safely, and cannot
// run script. media's ResourceMarkdown tests, with food's plain matchers.
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import Markdown from './Markdown'

afterEach(cleanup)

describe('Markdown', () => {
  it('renders an inline link inside a sentence', () => {
    render(<Markdown>{'Read [the guide](https://example.com/guide) first.'}</Markdown>)
    const link = screen.getByRole('link', { name: 'the guide' })
    expect(link.getAttribute('href')).toBe('https://example.com/guide')
    expect(link.closest('p').textContent).toBe('Read the guide first.')
  })

  it('opens links in a new tab without handing over the opener', () => {
    render(<Markdown>{'[x](https://example.com)'}</Markdown>)
    const link = screen.getByRole('link', { name: 'x' })
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toBe('noopener noreferrer')
  })

  it('autolinks a bare URL', () => {
    render(<Markdown>{'See https://example.org/page for more'}</Markdown>)
    expect(screen.getByRole('link', { name: 'https://example.org/page' }).getAttribute('href')).toBe(
      'https://example.org/page',
    )
  })

  it('does not render a javascript: link as an executable href', () => {
    const { container } = render(<Markdown>{'[click me](javascript:alert(1))'}</Markdown>)
    // The mirror case is the inline-link test above: the same markup with a
    // real URL does produce an href, so an absent one here is the sanitiser's.
    const anchors = container.querySelectorAll('a')
    expect(anchors.length).toBeLessThanOrEqual(1)
    anchors.forEach((a) => {
      expect(a.getAttribute('href') || '').not.toMatch(/^\s*javascript:/i)
    })
    expect(container.textContent).toContain('click me')
  })

  it('drops raw HTML rather than rendering it', () => {
    const { container } = render(<Markdown>{'<img src="x" onerror="alert(1)"> <b>bold</b>'}</Markdown>)
    expect(container.querySelector('img')).toBeNull()
    expect(container.querySelector('b')).toBeNull()
  })

  it('renders Markdown structure, so the drop above is of HTML and not of everything', () => {
    const { container } = render(<Markdown>{'**bold** and\n\n- one\n- two'}</Markdown>)
    expect(container.querySelector('strong').textContent).toBe('bold')
    expect(container.querySelectorAll('li')).toHaveLength(2)
  })
})
