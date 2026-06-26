import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { expandWikilinks } from '../lib/wikiLinks'

export function MarkdownViewer({
  content,
  className = '',
  onWikiLink,
}: {
  content: string
  className?: string
  onWikiLink?: (slug: string, label: string) => void
}) {
  const prepared = expandWikilinks(content)

  return (
    <div className={`markdown-viewer ${className}`.trim()}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="markdown-viewer__h1">{children}</h1>,
          h2: ({ children }) => <h2 className="markdown-viewer__h2">{children}</h2>,
          h3: ({ children }) => <h3 className="markdown-viewer__h3">{children}</h3>,
          p: ({ children }) => <p className="markdown-viewer__p">{children}</p>,
          ul: ({ children }) => <ul className="markdown-viewer__ul">{children}</ul>,
          ol: ({ children }) => <ol className="markdown-viewer__ol">{children}</ol>,
          li: ({ children }) => <li className="markdown-viewer__li">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="markdown-viewer__blockquote">{children}</blockquote>
          ),
          a: ({ href, children }) => {
            if (href?.startsWith('portolan://') && onWikiLink) {
              const slug = decodeURIComponent(href.slice('portolan://'.length))
              const label = String(children)
              return (
                <button
                  type="button"
                  className="markdown-viewer__wiki-link"
                  onClick={() => onWikiLink(slug, label)}
                >
                  {children}
                </button>
              )
            }
            return (
              <a href={href} className="markdown-viewer__link" target="_blank" rel="noreferrer">
                {children}
              </a>
            )
          },
          code: ({ className: codeClass, children }) => {
            const inline = !codeClass
            return inline ? (
              <code className="markdown-viewer__code-inline">{children}</code>
            ) : (
              <code className={`markdown-viewer__code-block ${codeClass ?? ''}`}>{children}</code>
            )
          },
          pre: ({ children }) => <pre className="markdown-viewer__pre">{children}</pre>,
          table: ({ children }) => (
            <div className="markdown-viewer__table-wrap">
              <table className="markdown-viewer__table">{children}</table>
            </div>
          ),
        }}
      >
        {prepared}
      </ReactMarkdown>
    </div>
  )
}
