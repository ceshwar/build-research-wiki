import { useState } from 'react'
import type { DockPreflightFile } from '../api/client'

export type DockFilePolicy = {
  filename: string
  action: 'upload' | 'skip' | 'replace' | 'merge'
  merge_into_slug?: string
  merge_fields?: Record<string, 'existing' | 'new' | 'concatenate'>
}

type RowState = {
  action: 'upload' | 'skip' | 'replace' | 'merge'
  mergeSlug: string
  title: 'existing' | 'new'
  abstract: 'existing' | 'new' | 'concatenate'
  pdf: 'existing' | 'new'
}

export function DuplicateUploadModal({
  files,
  onCancel,
  onConfirm,
}: {
  files: DockPreflightFile[]
  onCancel: () => void
  onConfirm: (policies: DockFilePolicy[]) => void
}) {
  const conflictFiles = files.filter((f) => f.matches.length > 0)
  const [rows, setRows] = useState<Record<string, RowState>>(() => {
    const init: Record<string, RowState> = {}
    for (const f of conflictFiles) {
      init[f.filename] = {
        action: 'skip',
        mergeSlug: f.matches[0]?.slug ?? '',
        title: 'existing',
        abstract: 'concatenate',
        pdf: 'new',
      }
    }
    return init
  })

  if (conflictFiles.length === 0) return null

  const setRow = (filename: string, patch: Partial<RowState>) => {
    setRows((prev) => ({ ...prev, [filename]: { ...prev[filename], ...patch } }))
  }

  return (
    <div className="dup-modal" role="dialog" aria-labelledby="dup-modal-title">
      <div className="dup-modal__card">
        <h3 id="dup-modal-title">Possible duplicates</h3>
        <p className="dup-modal__lead">
          These uploads match papers already on your chart. Choose how to handle each file.
        </p>
        <ul className="dup-modal__list">
          {conflictFiles.map((f) => {
            const row = rows[f.filename]
            const match = f.matches.find((m) => m.slug === row.mergeSlug) ?? f.matches[0]
            return (
              <li key={f.filename} className="dup-modal__item">
                <div className="dup-modal__file">
                  <strong>{f.filename}</strong>
                  {f.preprint && (
                    <span className="dup-modal__tag">arXiv (preprint)</span>
                  )}
                </div>
                <p className="dup-modal__match">
                  Matches{' '}
                  <strong>{match?.title ?? 'chart entry'}</strong> ({match?.match_type})
                </p>
                {f.matches.length > 1 && (
                  <label className="dup-modal__field">
                    <span>Merge target</span>
                    <select
                      value={row.mergeSlug}
                      onChange={(e) => setRow(f.filename, { mergeSlug: e.target.value })}
                    >
                      {f.matches.map((m) => (
                        <option key={m.slug} value={m.slug}>
                          {m.title}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <label className="dup-modal__field">
                  <span>Action</span>
                  <select
                    value={row.action}
                    onChange={(e) =>
                      setRow(f.filename, { action: e.target.value as RowState['action'] })
                    }
                  >
                    <option value="skip">Skip — keep existing</option>
                    <option value="replace">Replace — overwrite file in dock</option>
                    <option value="merge">Merge into chart entry</option>
                  </select>
                </label>
                {row.action === 'merge' && (
                  <div className="dup-modal__merge-grid">
                    <label>
                      Title
                      <select
                        value={row.title}
                        onChange={(e) =>
                          setRow(f.filename, { title: e.target.value as RowState['title'] })
                        }
                      >
                        <option value="existing">Keep existing</option>
                        <option value="new">Use new PDF</option>
                      </select>
                    </label>
                    <label>
                      Abstract
                      <select
                        value={row.abstract}
                        onChange={(e) =>
                          setRow(f.filename, {
                            abstract: e.target.value as RowState['abstract'],
                          })
                        }
                      >
                        <option value="existing">Keep existing</option>
                        <option value="new">Use new</option>
                        <option value="concatenate">Concatenate both</option>
                      </select>
                    </label>
                    <label>
                      PDF file
                      <select
                        value={row.pdf}
                        onChange={(e) =>
                          setRow(f.filename, { pdf: e.target.value as RowState['pdf'] })
                        }
                      >
                        <option value="existing">Keep existing</option>
                        <option value="new">Use new upload</option>
                      </select>
                    </label>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
        <div className="dup-modal__actions">
          <button type="button" className="btn-secondary px-4 py-2 text-sm" onClick={onCancel}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-primary px-4 py-2 text-sm"
            onClick={() => {
              const policies: DockFilePolicy[] = conflictFiles.map((f) => {
                const row = rows[f.filename]
                if (row.action === 'merge') {
                  return {
                    filename: f.filename,
                    action: 'merge',
                    merge_into_slug: row.mergeSlug,
                    merge_fields: {
                      title: row.title,
                      abstract: row.abstract,
                      pdf: row.pdf,
                    },
                  }
                }
                return { filename: f.filename, action: row.action }
              })
              const clean = files
                .filter((f) => !f.matches.length)
                .map((f) => ({ filename: f.filename, action: 'upload' as const }))
              onConfirm([...policies, ...clean])
            }}
          >
            Continue upload
          </button>
        </div>
      </div>
    </div>
  )
}
