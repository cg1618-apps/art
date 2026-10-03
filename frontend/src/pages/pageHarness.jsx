// Frontend tests: the harness a page test runs the real routes in, with fetch
// mocked. notes, options and roadmap each carry their own copy of this; the
// exercise and record tests share this one.
//
//   stubFetch(respond)  replaces fetch; every call is recorded as
//                       { url (decoded), method, body (parsed) } and answered
//                       by respond(call). Returns the list of calls.
//   renderAt(path)      the app's routes at `path`, with a fresh query cache
//                       and a probe for the current location
//   currentLocation()   that probe's pathname + search
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { vi } from 'vitest'

import AppRoutes from '../routes'

export function json(body, status = 200) {
  return new Response(body === null ? null : JSON.stringify(body), { status })
}

export function stubFetch(respond) {
  const calls = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options = {}) => {
      const call = {
        url: decodeURIComponent(url),
        method: options.method ?? 'GET',
        body: typeof options.body === 'string' ? JSON.parse(options.body) : undefined,
      }
      calls.push(call)
      return respond(call)
    }),
  )
  return calls
}

// A test helper is never hot-reloaded, so mixing it with helpers costs nothing.
// oxlint-disable-next-line react/only-export-components
function LocationProbe() {
  const { pathname, search } = useLocation()
  return <output data-testid="location">{`${pathname}${search}`}</output>
}

export function renderAt(path) {
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

export const currentLocation = () => screen.getByTestId('location').textContent
