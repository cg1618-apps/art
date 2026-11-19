# The frontend foundation is `food`'s, not `media`'s

A deliberate divergence from the reference implementation. art's frontend is
`food`'s: one `client.js` that calls `fetch`, `endpoints.js`, `useApiQuery` /
`useApiMutation` over TanStack Query, `useUrlFilters`, react-router 7,
Tailwind 4 with `food`'s tokens, Vitest. `media`'s Options page uses raw
`fetch` in `useEffect` and react-router 6 — the older shape of the same ideas.

Markdown is the exception, and follows `media`: `food` has no renderer, so
`components/Markdown.jsx` is `media`'s `ResourceMarkdown` configuration —
`react-markdown` and `remark-gfm`, no raw HTML, `javascript:` links inert.
