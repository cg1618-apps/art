// The single source of URL truth. Import these instead of hardcoding
// '/api/...' strings in components.
//
// Each group's `list()` is also its RESOURCE PREFIX: every read of that
// resource is a URL under it, which is what useApiMutation's `invalidate`
// matches on. There is no /api/edit write prefix as in food: art is behind
// Cloudflare Access as a whole, so reads and writes share one path.

const API = '/api'

export const endpoints = {
  // 選項: the open vocabularies every module reads. `categories()` is the
  // registry in code (key, label, description); GET list() takes ?category=.
  // DELETE remove(id) takes ?in_use=<n>, the count the page showed, and is a
  // 409 { field: 'in_use', expected, actual } when it has moved.
  options: {
    categories: () => `${API}/options/categories`,
    list: () => `${API}/options`,
    create: () => `${API}/options`,
    update: (id) => `${API}/options/${id}`,
    remove: (id) => `${API}/options/${id}`,
  },
  // 筆記. GET list() takes ?q=, and repeated ?category_id= and ?topic_id=,
  // each "any of".
  notes: {
    list: () => `${API}/notes`,
    detail: (id) => `${API}/notes/${id}`,
    create: () => `${API}/notes`,
    update: (id) => `${API}/notes/${id}`,
    remove: (id) => `${API}/notes/${id}`,
  },
  health: () => '/health',
}

export { API }
