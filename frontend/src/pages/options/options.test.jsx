// The Options page through the real route, with fetch mocked: a section per
// registered category with its description, the values' table, add and edit in
// place, and the delete that states its count, sends it back, and corrects
// itself on a 409.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AppRoutes from '../../routes'

const CATEGORIES = [
  { key: 'note_category', label: '筆記分類', description: '筆記是哪一種知識。' },
  { key: 'method', label: '方法', description: '一次練習是怎麼畫的。' },
]

const OPTIONS = [
  { id: 1, category: 'note_category', value: '名詞', description: '一個詞的定義', remark: '自己用', sort_order: 0, in_use: 3 },
  { id: 2, category: 'method', value: '速寫', description: '限時快速畫', remark: null, sort_order: 0, in_use: 0 },
]

let calls
let handler

function json(body, status = 200) {
  return new Response(body === null ? null : JSON.stringify(body), { status })
}

function renderOptions() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/options']}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const optionReads = () => calls.filter((call) => call.method === 'GET' && call.url === '/api/options')

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
      const answer = handler(call)
      if (answer) return answer
      if (call.url === '/api/options/categories') return json(CATEGORIES)
      if (call.url === '/api/options') return json(OPTIONS)
      return json([])
    }),
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('the options page', () => {
  it('draws one section per category, its description, then its values', async () => {
    renderOptions()
    const section = await screen.findByRole('region', { name: '筆記分類' })
    expect(within(section).getByText('筆記是哪一種知識。')).toBeTruthy()
    const row = within(section).getByText('名詞').closest('tr')
    expect(row.textContent).toContain('一個詞的定義')
    expect(row.textContent).toContain('自己用')
    expect(row.textContent).toContain('3')
    // Grouped by category: a method value is not in the notes' section.
    expect(within(section).queryByText('速寫')).toBeNull()
    expect(within(screen.getByRole('region', { name: '方法' })).getByText('速寫')).toBeTruthy()
  })

  it('adds a value to its category, after the last one', async () => {
    handler = (call) => (call.method === 'POST' ? json({ id: 3 }, 201) : null)
    renderOptions()
    const section = await screen.findByRole('region', { name: '方法' })
    fireEvent.click(within(section).getByRole('button', { name: /新增方法/ }))
    fireEvent.change(within(section).getByRole('textbox', { name: '新方法的 值' }), { target: { value: ' 描寫 ' } })
    fireEvent.click(within(section).getByRole('button', { name: '新增' }))
    await waitFor(() => expect(calls.some((call) => call.method === 'POST')).toBe(true))
    expect(calls.find((call) => call.method === 'POST').body).toEqual({
      category: 'method',
      value: '描寫',
      description: null,
      remark: null,
      sort_order: 1,
    })
  })

  it('edits a value in place without sending its category', async () => {
    handler = (call) => (call.method === 'PATCH' ? json(OPTIONS[0]) : null)
    renderOptions()
    fireEvent.click(await screen.findByRole('button', { name: '編輯「名詞」' }))
    fireEvent.change(screen.getByRole('textbox', { name: '「名詞」的 說明' }), { target: { value: '定義' } })
    fireEvent.click(screen.getByRole('button', { name: '儲存' }))
    await waitFor(() => expect(calls.some((call) => call.method === 'PATCH')).toBe(true))
    const patch = calls.find((call) => call.method === 'PATCH')
    expect(patch.url).toBe('/api/options/1')
    expect(patch.body).toEqual({ value: '名詞', description: '定義', remark: '自己用', sort_order: 0 })
  })

  it('states the count, sends it, and on a 409 shows the server and the new count', async () => {
    let deletes = 0
    handler = (call) => {
      if (call.method !== 'DELETE') return null
      deletes += 1
      if (deletes === 1) {
        return json({ detail: '使用數已經變了。', field: 'in_use', expected: 3, actual: 5 }, 409)
      }
      return json(null, 204)
    }
    renderOptions()
    fireEvent.click(await screen.findByRole('button', { name: '刪除「名詞」' }))
    const dialog = screen.getByRole('dialog')
    expect(dialog.textContent).toContain('3 處用到它')

    const readsBefore = optionReads().length
    fireEvent.click(within(dialog).getByRole('button', { name: '刪除' }))
    expect(await within(dialog).findByText('使用數已經變了。')).toBeTruthy()
    expect(dialog.textContent).toContain('5 處用到它')
    expect(calls.find((call) => call.method === 'DELETE').url).toBe('/api/options/1?in_use=3')
    // The page refetches behind the dialog.
    await waitFor(() => expect(optionReads().length).toBeGreaterThan(readsBefore))

    fireEvent.click(within(dialog).getByRole('button', { name: '確認刪除' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(calls.filter((call) => call.method === 'DELETE').at(-1).url).toBe('/api/options/1?in_use=5')
  })
})
