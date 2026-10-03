// Thin wrappers over TanStack Query so that no component builds a query key or
// a fetch call by hand. The cache key is an array of [url, params], which is
// what makes a filter change a refetch rather than a stale render. food's
// shape, without its image upload.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { buildUrl, fetchJson, jsonBody } from '../api/client'
import { endpoints } from '../api/endpoints'

export function useApiQuery(url, params, options = {}) {
  return useQuery({
    queryKey: [url, params ?? null],
    queryFn: () => fetchJson(buildUrl(url, params)),
    staleTime: 30_000,
    ...options,
  })
}

/**
 * Whether a cached query's URL is a read of the resource at `prefix`.
 *
 * Whole path segments only: `/api/notes` covers `/api/notes`,
 * `/api/notes?q=...` and `/api/notes/3`, and not a URL that merely begins with
 * the same letters.
 */
export function isUnderResource(url, prefix) {
  if (typeof url !== 'string') return false
  return url === prefix || url.startsWith(`${prefix}/`) || url.startsWith(`${prefix}?`)
}

/**
 * A mutation that invalidates by RESOURCE, not by one URL.
 *
 * `invalidate` is a list of read prefixes - each group's `list()` in
 * api/endpoints.js. Every cached query whose URL sits under one of them is
 * invalidated. Name every resource whose reads the write changes: an option
 * rename shows on every note that carries it.
 *
 * Call as `mutation.mutateAsync({ url, body })`; `body` is sent as JSON.
 */
export function useApiMutation({ method = 'POST', invalidate = [] } = {}) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ url, body }) =>
      fetchJson(url, { method, ...(body === undefined ? {} : jsonBody(body)) }),
    onSuccess: () => invalidateResources(queryClient, invalidate),
  })
}

/**
 * Invalidate every cached read under any of `prefixes`. `options` passes
 * through to TanStack's invalidateQueries - `{ refetchType: 'none' }` marks
 * them stale without refetching what is on screen, for a delete whose own
 * detail read would only 404 if refetched before the page leaves.
 */
export function invalidateResources(queryClient, prefixes, options) {
  if (!prefixes.length) return Promise.resolve()
  return queryClient.invalidateQueries(
    {
      predicate: (query) => prefixes.some((prefix) => isUnderResource(query.queryKey[0], prefix)),
    },
    options,
  )
}

/**
 * The option categories the code registers, `[{ key, label, description }]`.
 * Read once per page load: the registry changes only with a deploy.
 */
export function useOptionCategories() {
  return useApiQuery(endpoints.options.categories(), null, {
    staleTime: Infinity,
    gcTime: Infinity,
  })
}

/** Every option of one category, `[Option]`, in the server's order. */
export function useOptions(category) {
  return useApiQuery(endpoints.options.list(), { category })
}
