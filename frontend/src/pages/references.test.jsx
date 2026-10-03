// The References pages through the real routes, with fetch mocked: the
// library's filters come from and go to the URL and reach the API as repeated
// ids and no_group; a card's name opens the link itself in a new tab; the
// detail renders the notes as Markdown; the form sends the API's
// ReferenceWrite shape.
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { currentLocation, json, renderAt, stubFetch } from './pageHarness'

const GROUPS = [
  { id: 20, category: 'reference_group', value: '表情', description: '臉部表情', remark: null, sort_order: 0, in_use: 1 },
  { id: 21, category: 'reference_group', value: '配件', description: null, remark: null, sort_order: 1, in_use: 0 },
]

const ref = ({ id, value, description }) => ({ id, value, description })

const SUMMARY = {
  id: 5,
  name: '表情參考集',
  url: 'https://www.example.com/faces?page=2',
  groups: [ref(GROUPS[0])],
  notes_excerpt: '看眉毛和嘴角 **怎麼動**',
  updated_at: '2026-10-03T00:00:00Z',
}

const REFERENCE = {
  id: 5,
  name: '表情參考集',
  url: 'https://www.example.com/faces?page=2',
  groups: [ref(GROUPS[0])],
  notes: '看眉毛和嘴角 **怎麼動**\n\n<script>alert(1)</script>',
  created_at: '2026-10-03T00:00:00Z',
  updated_at: '2026-10-03T00:00:00Z',
}

let calls
let handler

function defaultResponse(call) {
  const [path] = call.url.split('?')
  if (path === '/api/options') return json(GROUPS)
  if (path === '/api/references') return json([SUMMARY])
  if (path === '/api/references/5') return json(REFERENCE)
  if (path === '/api/timer') return json(null)
  return json([])
}

const listRequests = () =>
  calls.filter((call) => call.method === 'GET' && call.url.split('?')[0] === '/api/references').map((c) => c.url)

beforeEach(() => {
  handler = () => null
  calls = stubFetch((call) => handler(call) ?? defaultResponse(call))
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('the references library', () => {
  it('shows each reference: its name opens the link, then host, groups, excerpt and detail', async () => {
    renderAt('/references')
    const list = await screen.findByRole('list', { name: '參考' })
    const link = within(list).getByRole('link', { name: '表情參考集' })
    expect(link.getAttribute('href')).toBe('https://www.example.com/faces?page=2')
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toBe('noopener noreferrer')
    expect(within(list).getByText('www.example.com')).toBeTruthy()
    expect(within(list).getByText('表情')).toBeTruthy()
    expect(within(list).getByText('看眉毛和嘴角 **怎麼動**')).toBeTruthy()
    const detail = within(list).getByRole('link', { name: '表情參考集 的詳細' })
    expect(detail.getAttribute('href')).toBe('/references/5')
  })

  it('reads the filters from the URL and sends them as repeated ids', async () => {
    renderAt('/references?group=20&group=21')
    await waitFor(() => expect(listRequests()).toContain('/api/references?group_id=20&group_id=21'))
    const sidebar = screen.getByRole('complementary', { name: '篩選' })
    expect(await within(sidebar).findByRole('button', { name: '表情', pressed: true })).toBeTruthy()
    expect(within(sidebar).getByRole('button', { name: '未分組', pressed: false })).toBeTruthy()
  })

  it('writes a group click and 未分組 to the URL and refetches with them', async () => {
    renderAt('/references')
    const sidebar = screen.getByRole('complementary', { name: '篩選' })
    fireEvent.click(await within(sidebar).findByRole('button', { name: '配件' }))
    expect(currentLocation()).toBe('/references?group=21')
    await waitFor(() => expect(listRequests()).toContain('/api/references?group_id=21'))

    fireEvent.click(within(sidebar).getByRole('button', { name: '未分組' }))
    expect(currentLocation()).toBe('/references?group=21&ungrouped=1')
    await waitFor(() => expect(listRequests()).toContain('/api/references?group_id=21&no_group=true'))
  })

  it('offers clearing when only the filters leave it empty', async () => {
    handler = (call) => (call.url.startsWith('/api/references?') ? json([]) : null)
    renderAt('/references?q=不存在')
    expect(await screen.findByText('沒有符合條件的參考。')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '清除搜尋與篩選' }))
    expect(currentLocation()).toBe('/references')
  })

  it('is in the navigation as 參考', async () => {
    renderAt('/references')
    const navs = await screen.findAllByRole('navigation', { name: '主要' })
    for (const nav of navs) {
      const item = within(nav).getByRole('link', { name: '參考' })
      expect(item.getAttribute('aria-current')).toBe('page')
    }
  })
})

describe('a reference', () => {
  it('shows the link, the groups and the notes as Markdown with raw HTML dropped', async () => {
    renderAt('/references/5')
    expect(await screen.findByRole('heading', { level: 1, name: '表情參考集' })).toBeTruthy()
    const link = screen.getByRole('link', { name: /www\.example\.com\/faces/ })
    expect(link.getAttribute('href')).toBe('https://www.example.com/faces?page=2')
    expect(link.getAttribute('rel')).toBe('noopener noreferrer')
    expect(screen.getByRole('link', { name: '表情' }).getAttribute('href')).toBe('/references?group=20')
    expect(screen.getByText('怎麼動').tagName).toBe('STRONG')
    expect(document.querySelector('article script')).toBeNull()
  })

  it('deletes through the dialog and returns to the library', async () => {
    handler = (call) => (call.method === 'DELETE' ? json(null, 204) : null)
    renderAt('/references/5')
    fireEvent.click(await screen.findByRole('button', { name: '刪除' }))
    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: '刪除' }))
    await waitFor(() => expect(currentLocation()).toBe('/references'))
    expect(calls.some((call) => call.method === 'DELETE' && call.url === '/api/references/5')).toBe(true)
  })
})

describe('the reference form', () => {
  it('sends a new reference in the API shape and goes to its page', async () => {
    handler = (call) => (call.method === 'POST' ? json({ ...REFERENCE, id: 9 }, 201) : null)
    renderAt('/references/new')

    fireEvent.change(screen.getByRole('textbox', { name: '名稱' }), { target: { value: ' 手 ' } })
    fireEvent.change(screen.getByRole('textbox', { name: /網址/ }), { target: { value: 'example.com/hands' } })
    fireEvent.click(await screen.findByRole('button', { name: '表情' }))
    // The picker shows the chosen option's description.
    expect(screen.getByText('臉部表情')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '配件' }))
    fireEvent.change(screen.getByRole('textbox', { name: /^筆記/ }), { target: { value: '看手指' } })
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))

    await waitFor(() => expect(currentLocation()).toBe('/references/9'))
    const post = calls.find((call) => call.method === 'POST')
    expect(post.url).toBe('/api/references')
    expect(post.body).toEqual({
      name: '手',
      url: 'example.com/hands',
      group_ids: [20, 21],
      notes: '看手指',
    })
  })

  it('refuses a reference with no name or no link without sending it', async () => {
    renderAt('/references/new')
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    expect(await screen.findByText('請填寫名稱。')).toBeTruthy()
    fireEvent.change(screen.getByRole('textbox', { name: '名稱' }), { target: { value: '手' } })
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    expect(await screen.findByText('請填寫連結。')).toBeTruthy()
    expect(calls.some((call) => call.method === 'POST')).toBe(false)
  })

  it('loads an existing reference and PATCHes it, replacing the groups', async () => {
    handler = (call) => (call.method === 'PATCH' ? json(REFERENCE) : null)
    renderAt('/references/5/edit')
    expect(await screen.findByDisplayValue('表情參考集')).toBeTruthy()
    fireEvent.click(await screen.findByRole('button', { name: '表情', pressed: true }))
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(currentLocation()).toBe('/references/5'))
    const patch = calls.find((call) => call.method === 'PATCH')
    expect(patch.url).toBe('/api/references/5')
    expect(patch.body).toEqual({
      name: '表情參考集',
      url: 'https://www.example.com/faces?page=2',
      group_ids: [],
      notes: '看眉毛和嘴角 **怎麼動**\n\n<script>alert(1)</script>',
    })
  })
})
