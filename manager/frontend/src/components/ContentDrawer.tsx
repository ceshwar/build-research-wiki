import { useCallback, useEffect, useState } from 'react'
import { fetchVaultFile, vaultFileRawUrl } from '../api/client'
import { prepareWikiMarkdown, resolveWikiPath, type WikiPathResolver } from '../lib/wikiLinks'
import { MarkdownViewer } from './MarkdownViewer'

type DrawerFrame = { path: string; title?: string }

export function ContentDrawer({
  vaultId,
  path,
  title,
  wikiResolver,
  onClose,
}: {
  vaultId: string
  path: string
  title?: string
  wikiResolver?: WikiPathResolver
  onClose: () => void
}) {
  const [stack, setStack] = useState<DrawerFrame[]>([{ path, title }])
  const [content, setContent] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const frame = stack[stack.length - 1]

  useEffect(() => {
    setStack([{ path, title }])
  }, [path, title, vaultId])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setPdfUrl(null)
    setContent(null)
    fetchVaultFile(vaultId, frame.path)
      .then((data) => {
        if (cancelled) return
        if (data.content_type === 'application/pdf') {
          setPdfUrl(vaultFileRawUrl(vaultId, frame.path))
        } else {
          setContent(prepareWikiMarkdown(data.content || ''))
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Could not load file')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [vaultId, frame.path])

  const onWikiLink = useCallback(
    (slug: string, label: string) => {
      const next = resolveWikiPath(slug, wikiResolver)
      setStack((s) => [...s, { path: next, title: label }])
    },
    [wikiResolver],
  )

  const canBack = stack.length > 1
  const displayTitle = frame.title || frame.path.split('/').pop() || frame.path

  return (
    <aside className="content-drawer" role="dialog" aria-label={displayTitle}>
      <header className="content-drawer__header">
        <div className="content-drawer__meta">
          {canBack && (
            <button type="button" className="content-drawer__back" onClick={() => setStack((s) => s.slice(0, -1))}>
              ← Back
            </button>
          )}
          <div className="content-drawer__title">{displayTitle}</div>
          <div className="content-drawer__path">{frame.path}</div>
        </div>
        <button type="button" className="content-drawer__close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </header>
      <div className="content-drawer__body">
        {loading && (
          <div className="content-drawer__loading" role="status">
            <span className="spinner" aria-hidden="true" />
            Loading…
          </div>
        )}
        {error && <p className="content-drawer__error">{error}</p>}
        {pdfUrl && !loading && (
          <div className="content-drawer__pdf-wrap">
            <div className="content-drawer__pdf-actions">
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary px-3 py-1 text-xs"
              >
                Open in new tab
              </a>
            </div>
            <iframe className="content-drawer__pdf" src={pdfUrl} title={displayTitle} />
          </div>
        )}
        {content != null && <MarkdownViewer content={content} onWikiLink={onWikiLink} />}
      </div>
    </aside>
  )
}
