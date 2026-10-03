// Frontend: the two defaults a new record's form starts with - the newest
// record's location and the Clip Studio Paint tool (lib/records.js) - for the
// record form and the timer's record draft.
//
// { defaults: { location_id, tool_id }, isPending } - isPending until both
// are known, so a save does not resolve an UNCHOSEN field to a default that
// has not loaded. `enabled` false skips the records read (an existing
// record's form has no defaults to apply).
import { endpoints } from '../api/endpoints'
import { defaultToolId, latestLocationId } from '../lib/records'
import { useApiQuery, useOptions } from './useApi'

export function useRecordDefaults({ enabled = true } = {}) {
  // The newest record: the list is newest first.
  const latest = useApiQuery(endpoints.records.list(), null, { enabled })
  const tools = useOptions('tool')
  return {
    defaults: { location_id: latestLocationId(latest.data), tool_id: defaultToolId(tools.data) },
    isPending: latest.isPending || tools.isPending,
  }
}
