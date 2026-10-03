// Frontend: what a page may do with a URL it was given.
//
// Only an http(s) URL becomes a link; anything else - a javascript: URL among
// them - is shown as text, as the Markdown renderer would leave it. The server
// refuses other schemes on every write, so this is the second line, not the
// first. Shared by ResourceList and the reference pages.

/** True for an http or https URL. */
export function isWebLink(url) {
  return /^https?:\/\//i.test(url ?? '')
}

/** The host a URL points at (`www.example.com`), or the URL itself when it does not parse. */
export function hostOf(url) {
  try {
    return new URL(url).host || url
  } catch {
    return url
  }
}
