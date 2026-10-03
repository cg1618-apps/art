// Frontend: a thing's resources as links, under a 資源 heading (or `title`).
//
// The read side of components/forms/ResourceRows.jsx, shared by every detail
// page that has resources (a note, a stage). Draws nothing when there are none.
//
// Only an http(s) URL becomes a link, opened in a new tab; anything else - a
// javascript: URL among them - is shown as text (lib/links.js).
import { hostOf, isWebLink } from '../lib/links'
import { Section } from './ui/primitives'

// A resource's words: its name, else the link's host, else the link.
function resourceLabel(resource) {
  return resource.name || hostOf(resource.url)
}

export default function ResourceList({ resources, title = '資源', as }) {
  if (!resources?.length) return null
  return (
    <Section title={title} as={as}>
      <ul className="space-y-1">
        {resources.map((resource) => (
          <li key={resource.id ?? resource.url}>
            {isWebLink(resource.url) ? (
              <a href={resource.url} target="_blank" rel="noopener noreferrer" className="text-brand hover:underline">
                {resourceLabel(resource)} ↗
              </a>
            ) : (
              <span className="text-text-muted">
                {resource.name ? `${resource.name}: ` : ''}
                {resource.url}
              </span>
            )}
          </li>
        ))}
      </ul>
    </Section>
  )
}
