// Frontend: the sections of the app and which one a path belongs to.
//
// food's shape. The navigation is 路線圖 · 筆記 · 選項; each later module adds
// one entry here, and both navigation bars draw from this list.

export const SECTIONS = [
  { key: 'roadmap', label: '路線圖', to: '/roadmap', prefixes: ['/roadmap'] },
  { key: 'notes', label: '筆記', to: '/notes', prefixes: ['/notes'] },
  { key: 'options', label: '選項', to: '/options', prefixes: ['/options'] },
]

function underPrefix(pathname, prefix) {
  return pathname === prefix || pathname.startsWith(`${prefix}/`)
}

/** The key of the section `pathname` belongs to, or null. */
export function activeSection(pathname) {
  const section = SECTIONS.find((s) => s.prefixes.some((p) => underPrefix(pathname, p)))
  return section ? section.key : null
}
