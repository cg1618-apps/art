// Frontend: renders a note's Markdown body.
//
// media's ResourceMarkdown, copied. react-markdown builds React elements,
// never HTML strings, and without rehype-raw any raw HTML in the source is
// dropped rather than rendered. Its default urlTransform is kept on purpose:
// it blanks any link whose protocol is not http(s), mailto, irc(s) or xmpp, so
// a `javascript:` link renders inert. remark-gfm adds autolinked bare URLs,
// tables, strikethrough and task lists.
//
// Both matter before anything is published: a note may become public under
// /s/... one day, and its body is then read by people who did not write it.
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const REMARK_PLUGINS = [remarkGfm]

// Every link leaves the site: a note points somewhere else.
function ExternalLink({ node: _node, children, ...props }) {
  return (
    <a {...props} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  )
}

const COMPONENTS = { a: ExternalLink }

// Descendant styling in tokens only - there is no typography plugin, and
// theme-tokens.test.js refuses hard-coded greys.
const PROSE_CLS = [
  'text-base text-text leading-relaxed break-words',
  '[&_p]:my-2 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
  '[&_a]:text-brand [&_a]:underline [&_a]:underline-offset-2 [&_a:hover]:text-brand-hover',
  '[&_ul]:list-disc [&_ol]:list-decimal [&_ul]:pl-5 [&_ol]:pl-5 [&_ul]:my-2 [&_ol]:my-2 [&_li]:my-0.5',
  '[&_h1]:font-display [&_h2]:font-display [&_h3]:font-display [&_h1]:font-bold [&_h2]:font-bold [&_h3]:font-bold [&_h1]:text-xl [&_h2]:text-lg [&_h3]:text-base [&_h1]:mt-4 [&_h2]:mt-4 [&_h3]:mt-3',
  '[&_code]:font-mono [&_code]:text-sm [&_code]:bg-surface-2 [&_code]:px-1 [&_code]:rounded-sm',
  '[&_pre]:bg-surface-2 [&_pre]:border [&_pre]:border-border [&_pre]:rounded-md [&_pre]:p-2 [&_pre]:overflow-x-auto [&_pre_code]:px-0',
  '[&_blockquote]:border-l-2 [&_blockquote]:border-border-strong [&_blockquote]:pl-3 [&_blockquote]:text-text-muted',
  '[&_hr]:border-border [&_hr]:my-4',
  '[&_table]:text-sm [&_th]:border [&_td]:border [&_th]:border-border [&_td]:border-border [&_th]:px-2 [&_td]:px-2 [&_th]:py-1 [&_td]:py-1 [&_th]:text-left',
].join(' ')

export default function Markdown({ children }) {
  return (
    <div className={PROSE_CLS}>
      <ReactMarkdown remarkPlugins={REMARK_PLUGINS} components={COMPONENTS}>
        {children || ''}
      </ReactMarkdown>
    </div>
  )
}
