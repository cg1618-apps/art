// The Notes pages through the real routes, with fetch mocked: the library's
// filters come from and go to the URL and reach the API as repeated ids; the
// detail renders the body as Markdown and resources as links; the form sends
// the API's NoteWrite shape.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AppRoutes from '../routes'

const CATEGORIES = [
  { id: 1, category: 'note_category', value: '名詞', description: '一個詞的定義', remark: null, sort_order: 0, in_use: 1 },
  { id: 2, category: 'note_category', value: '小技巧', description: null, remark: null, sort_order: 1, in_use: 0 },
]

const TOPICS = [
  { id: 10, category: 'topic', value: '透視', description: '空間的遠近', remark: null, sort_order: 0, in_use: 1 },
  { id: 11, category: 'topic', value: '線條', description: null, remark: null, sort_order: 1, in_use: 0 },
]

const ref = ({ id, value, description }) => ({ id, value, description })

const NOTE = {
  id: 7,
  display_name: '消失點',
  name_cn: '消失點',
  name_en: 'Vanishing point',
  name_alt: null,
  category: ref(CATEGORIES[0]),
  topics: [ref(TOPICS[0])],
  summary: '平行線在遠方交會的點。',
  visibility: 'private',
  updated_at: '2026-10-03T00:00:00Z',
  aliases: ['VP'],
  body: '**重點**\n\n<script>alert(1)</script>',
  remark: null,
  resources: [
    { id: 1, name: '教學', url: 'https://example.com/vp' },
    { id: 2, name: null, url: 'javascript:alert(1)' },
  ],
  created_at: '2026-10-03T00:00:00Z',
}

let calls
let handler

function json(body, status = 200) {
  return new Response(body === null ? null : JSON.stringify(body), { status })
}

// Answers a GET by path; `handler` may answer anything first.
function defaultResponse(call) {
  const [path, query = ''] = call.url.split('?')
  if (path === '/api/options') {
    if (query.includes('category=note_category')) return json(CATEGORIES)
    if (query.includes('category=topic')) return json(TOPICS)
    return json([...CATEGORIES, ...TOPICS])
  }
  if (path === '/api/notes') return json([NOTE])
  if (path === '/api/notes/7') return json(NOTE)
  return json([])
}

function LocationProbe() {
  const { pathname, search } = useLocation()
  return <output data-testid="location">{`${pathname}${search}`}</output>
}

function renderAt(path) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const location = () => screen.getByTestId('location').textContent
const listRequests = () =>
  calls.filter((call) => call.method === 'GET' && call.url.split('?')[0] === '/api/notes').map((c) => c.url)

beforeEach(() => {
  calls = []
  handler = () => null
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options = {}) => {
      const call = {
        url: decodeURIComponent(url),
        method: options.method ?? 'GET',
        body: typeof options.body === 'string' ? JSON.parse(options.body) : undefined,
      }
      calls.push(call)
      return handler(call) ?? defaultResponse(call)
    }),
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('the notes library', () => {
  it('shows each note with its category, topics and summary', async () => {
    renderAt('/notes')
    const list = await screen.findByRole('list', { name: '筆記' })
    const card = within(list).getByRole('link', { name: /消失點/ })
    expect(card.getAttribute('href')).toBe('/notes/7')
    expect(within(card).getByText('名詞')).toBeTruthy()
    expect(within(card).getByText('透視')).toBeTruthy()
    expect(within(card).getByText('平行線在遠方交會的點。')).toBeTruthy()
  })

  it('reads the filters from the URL and sends them as repeated ids', async () => {
    renderAt('/notes?topic=10&topic=11&category=1')
    await waitFor(() =>
      expect(listRequests()).toContain('/api/notes?category_id=1&topic_id=10&topic_id=11'),
    )
    const sidebar = screen.getByRole('complementary', { name: '篩選' })
    expect(await within(sidebar).findByRole('button', { name: '透視', pressed: true })).toBeTruthy()
  })

  it('writes a filter click to the URL and refetches with it', async () => {
    renderAt('/notes')
    const sidebar = screen.getByRole('complementary', { name: '篩選' })
    fireEvent.click(await within(sidebar).findByRole('button', { name: '線條' }))
    expect(location()).toBe('/notes?topic=11')
    await waitFor(() => expect(listRequests()).toContain('/api/notes?topic_id=11'))
  })

  it('offers clearing when only the filters leave it empty', async () => {
    handler = (call) => (call.url.startsWith('/api/notes?') ? json([]) : null)
    renderAt('/notes?q=不存在')
    expect(await screen.findByText('沒有符合條件的筆記。')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '清除搜尋與篩選' }))
    expect(location()).toBe('/notes')
  })
})

describe('a note', () => {
  it('renders the body as Markdown with raw HTML dropped', async () => {
    renderAt('/notes/7')
    expect(await screen.findByRole('heading', { level: 1, name: '消失點' })).toBeTruthy()
    expect(screen.getByText('重點').tagName).toBe('STRONG')
    expect(document.querySelector('article script')).toBeNull()
  })

  it('links an http resource and leaves a javascript: one as text', async () => {
    renderAt('/notes/7')
    const link = await screen.findByRole('link', { name: /教學/ })
    expect(link.getAttribute('href')).toBe('https://example.com/vp')
    expect(link.getAttribute('rel')).toBe('noopener noreferrer')
    expect(screen.getByText('javascript:alert(1)').closest('a')).toBeNull()
  })

  it('deletes through the dialog and returns to the library', async () => {
    handler = (call) => (call.method === 'DELETE' ? json(null, 204) : null)
    renderAt('/notes/7')
    fireEvent.click(await screen.findByRole('button', { name: '刪除' }))
    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: '刪除' }))
    await waitFor(() => expect(location()).toBe('/notes'))
    expect(calls.some((call) => call.method === 'DELETE' && call.url === '/api/notes/7')).toBe(true)
  })
})

describe('the note form', () => {
  it('sends a new note in the API shape and goes to its page', async () => {
    handler = (call) => (call.method === 'POST' ? json({ ...NOTE, id: 9 }, 201) : null)
    renderAt('/notes/new')

    fireEvent.change(screen.getByRole('textbox', { name: '中文名' }), { target: { value: ' 透視線 ' } })
    fireEvent.change(screen.getByRole('textbox', { name: /別名/ }), {
      target: { value: 'a，b、A\nc' },
    })
    fireEvent.click(await screen.findByRole('button', { name: '名詞' }))
    // The picker shows the chosen option's description.
    expect(screen.getByText('一個詞的定義')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '透視' }))
    fireEvent.click(screen.getByRole('button', { name: '線條' }))

    fireEvent.click(screen.getByRole('button', { name: /新增資源/ }))
    fireEvent.click(screen.getByRole('button', { name: /新增資源/ }))
    fireEvent.change(screen.getByRole('textbox', { name: '資源 1 連結' }), { target: { value: 'https://a.example' } })
    fireEvent.change(screen.getByRole('textbox', { name: '資源 2 名稱' }), { target: { value: '第二' } })
    fireEvent.change(screen.getByRole('textbox', { name: '資源 2 連結' }), { target: { value: 'https://b.example' } })
    fireEvent.click(screen.getByRole('button', { name: '上移資源 2' }))

    fireEvent.click(screen.getByRole('button', { name: '儲存' }))

    await waitFor(() => expect(location()).toBe('/notes/9'))
    const post = calls.find((call) => call.method === 'POST')
    expect(post.url).toBe('/api/notes')
    expect(post.body).toEqual({
      name_cn: '透視線',
      name_en: null,
      name_alt: null,
      aliases: ['a', 'b', 'c'],
      category_id: 1,
      topic_ids: [10, 11],
      summary: null,
      body: null,
      remark: null,
      visibility: 'private',
      resources: [
        { name: '第二', url: 'https://b.example' },
        { name: null, url: 'https://a.example' },
      ],
    })
  })

  it('refuses a note with no name without sending it', async () => {
    renderAt('/notes/new')
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    expect(await screen.findByText('至少要有一個名稱。')).toBeTruthy()
    expect(calls.some((call) => call.method === 'POST')).toBe(false)
  })

  it('loads an existing note and PATCHes it, clearing the category', async () => {
    handler = (call) => (call.method === 'PATCH' ? json(NOTE) : null)
    renderAt('/notes/7/edit')
    expect(await screen.findByDisplayValue('Vanishing point')).toBeTruthy()
    expect(screen.getByRole('textbox', { name: /別名/ }).value).toBe('VP')
    // Clicking the chosen category again clears it.
    fireEvent.click(await screen.findByRole('button', { name: '名詞', pressed: true }))
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(location()).toBe('/notes/7'))
    const patch = calls.find((call) => call.method === 'PATCH')
    expect(patch.url).toBe('/api/notes/7')
    expect(patch.body.category_id).toBeNull()
    expect(patch.body.topic_ids).toEqual([10])
    expect(patch.body.resources).toEqual([
      { name: '教學', url: 'https://example.com/vp' },
      { name: null, url: 'javascript:alert(1)' },
    ])
  })
})
