import { useEffect, useState } from 'react'
import { fetchVaultFile } from '../api/client'
import { MarkdownViewer } from './MarkdownViewer'

export function ContentDrawer({
  vaultId,
  path,
  title,
  onClose,
}: {
  vaultId: string
  path: string
  title?: string
  onClose: () => void
}) {
  const [content, setContent] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchVaultFile(vaultId, path)
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
  }, [vaultId, path])

  const displayTitle = title || path.split('/').pop() || path

  return (
    <aside className="content-drawer" role="dialog" aria-label={displayTitle}>
      <header className="content-drawer__header">
        <div className="content-drawer__meta">
          <div className="content-drawer__title">{displayTitle}</div>
          <div className="content-drawer__path">{path}</div>
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
        {content != null && <MarkdownViewer content={content} />}
      </div>
    </aside>
  )
}
