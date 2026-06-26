import { useCallback, useEffect, useState } from 'react'
import { fetchVaultFile } from '../api/client'
import { wikiPathForSlug, type WikiSlugHints } from '../lib/wikiLinks'
import { MarkdownViewer } from './MarkdownViewer'

type DrawerFrame = { path: string; title?: string }

export function ContentDrawer({
  vaultId,
  path,
  title,
  wikiHints,
  onClose,
}: {
  vaultId: string
  path: string
  title?: string
  wikiHints?: WikiSlugHints
  onClose: () => void
}) {
  const [stack, setStack] = useState<DrawerFrame[]>([{ path, title }])
  const [content, setContent] = useState<string | null>(null)
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
    fetchVaultFile(vaultId, frame.path)
      .then((data) => {
        if (cancelled) return
        if (data.content_type === 'application/pdf') {
          setContent(null)
          setError('PDF preview is not available in-app. Open the file from your reef folder.')
        } else {
          setContent(data.content || '')
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
      const next = wikiPathForSlug(slug, wikiHints)
      setStack((s) => [...s, { path: next, title: label }])
    },
    [wikiHints],
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
        {content != null && <MarkdownViewer content={content} onWikiLink={onWikiLink} />}
      </div>
    </aside>
  )
}
