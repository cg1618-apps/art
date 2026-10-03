// Frontend: the three visibilities a shareable thing carries, and their words.
//
// The values are the backend's `Visibility` enum (app/constants.py); nothing
// reads them yet, and everything is `private` until a sharing route exists.

export const VISIBILITIES = [
  { value: 'private', label: '私人' },
  { value: 'unlisted', label: '不公開列出' },
  { value: 'public', label: '公開' },
]

export const DEFAULT_VISIBILITY = 'private'

/** The word for `value`, or the value itself. */
export function visibilityLabel(value) {
  return VISIBILITIES.find((entry) => entry.value === value)?.label ?? value
}
