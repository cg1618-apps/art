// The two things every caller of the API needs: a readable message, and the
// status with the body for a caller that branches on a 409.
import { afterEach, describe, expect, it, vi } from 'vitest'

import { buildUrl, errorMessage, fetchJson } from './client'

afterEach(() => vi.unstubAllGlobals())

describe('buildUrl', () => {
  it('repeats the key for a list, as FastAPI reads list[int]', () => {
    expect(buildUrl('/api/notes', { topic_id: ['1', '2'], q: '線' })).toBe(
      '/api/notes?topic_id=1&topic_id=2&q=%E7%B7%9A',
    )
  })

  it('drops empty values, and the query with them', () => {
    expect(buildUrl('/api/notes', { q: '', category_id: null })).toBe('/api/notes')
  })
})

describe('errorMessage', () => {
  it('joins a validation array into a sentence naming each field', () => {
    const body = { detail: [{ loc: ['body', 'url'], msg: 'Field required' }] }
    expect(errorMessage(body, 'x')).toBe('url: Field required')
  })

  it('passes a hand-raised sentence through', () => {
    expect(errorMessage({ detail: '已經有這個選項。' }, 'x')).toBe('已經有這個選項。')
  })
})

describe('fetchJson', () => {
  it('throws with the status and the body, so a 409 can be read', async () => {
    const body = { detail: 'stale', field: 'in_use', expected: 1, actual: 3 }
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(body), { status: 409 })))
    const error = await fetchJson('/api/options/1?in_use=1', { method: 'DELETE' }).catch((e) => e)
    expect(error.status).toBe(409)
    expect(error.body.actual).toBe(3)
    expect(error.message).toBe('stale')
  })

  it('answers null for a 204', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(null, { status: 204 })))
    expect(await fetchJson('/api/notes/1', { method: 'DELETE' })).toBeNull()
  })
})
