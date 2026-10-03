// The only file in this application that calls fetch().
//
// food's client, without its Access sign-in handling: art sits behind
// Cloudflare Access as a whole, so there is no gated write prefix and no
// redirect a write could meet that a read would not.
//
// Everything else goes through these helpers, so that the two things every
// caller needs - a readable message and the status code - are produced in one
// place:
//
//   FastAPI's automatic validation error puts an ARRAY under `detail`, unlike
//   every hand-raised error. `new Error(array)` stringifies to
//   "[object Object]", so the array is joined into a sentence here.
//
//   The status and the body ride on the thrown Error, so a caller may branch
//   on a 409 - the option delete's stale count - without re-implementing fetch.

// An array value repeats its key - `{ topic_id: [1, 2] }` is
// `topic_id=1&topic_id=2` - which is how FastAPI reads a `list[int]` query
// parameter, and what the note list means by "any of".
export function buildUrl(url, params) {
  if (!params) return url
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    for (const item of Array.isArray(value) ? value : [value]) {
      if (item === undefined || item === null || item === '') continue
      search.append(key, String(item))
    }
  }
  const query = search.toString()
  return query ? `${url}?${query}` : url
}

export function errorMessage(body, fallback) {
  const detail = body?.detail
  if (Array.isArray(detail)) {
    // FastAPI validation errors: {loc, msg, type} per entry. The last element
    // of `loc` is the field name; the rest is request plumbing nobody reads.
    return (
      detail
        .map((entry) => {
          const field = Array.isArray(entry?.loc) ? entry.loc.at(-1) : null
          return field ? `${field}: ${entry.msg}` : entry?.msg
        })
        .filter(Boolean)
        .join('; ') || fallback
    )
  }
  if (typeof detail === 'string' && detail) return detail
  if (typeof body?.message === 'string' && body.message) return body.message
  return fallback
}

export async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  })

  if (response.status === 204) return null

  let body = null
  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    const error = new Error(errorMessage(body, response.statusText || `HTTP ${response.status}`))
    error.status = response.status
    error.body = body
    throw error
  }

  return body
}

export function jsonBody(body) {
  return { body: JSON.stringify(body) }
}
