import type { DropzoneInputProps, DropzoneRootProps } from 'react-dropzone'

type DockChannel = {
  emoji: string
  name: string
  extensions: string[]
}

export type DockUploadZoneProps = {
  variant: 'panel' | 'inline'
  channel?: DockChannel
  queuedFiles: File[]
  isDragActive: boolean
  getRootProps: <T extends DropzoneRootProps>(props?: T) => T
  getInputProps: <T extends DropzoneInputProps>(props?: T) => T
  uploadError: string | null
  isPending: boolean
  onConfirm: () => void
  mutationError?: string | null
  uploadedFiles?: { name: string; channel: string }[]
}

function extensionHint(channel?: DockChannel) {
  return channel?.extensions.map((e) => `.${e}`).join(', ') ?? '.pdf'
}

export function DockUploadZone({
  variant,
  channel,
  queuedFiles,
  isDragActive,
  getRootProps,
  getInputProps,
  uploadError,
  isPending,
  onConfirm,
  mutationError,
  uploadedFiles = [],
}: DockUploadZoneProps) {
  const hasStaged = queuedFiles.length > 0

  if (variant === 'inline') {
    return (
      <div className="dock-upload-inline-wrap">
        <div
          {...getRootProps()}
          className={`dock-upload-inline${isDragActive ? ' dock-upload-inline--active' : ''}${
            hasStaged ? ' dock-upload-inline--staged' : ''
          }`}
          title={`Drop ${extensionHint(channel)} to dock`}
        >
          <input {...getInputProps()} />
          {isDragActive ? (
            <span className="dock-upload-inline__label">Drop to dock</span>
          ) : hasStaged ? (
            <>
              <span className="dock-upload-inline__label">
                {queuedFiles.length} staged
              </span>
              <button
                type="button"
                className="dock-upload-inline__confirm"
                disabled={isPending}
                onClick={(e) => {
                  e.stopPropagation()
                  onConfirm()
                }}
              >
                {isPending ? '…' : 'Upload'}
              </button>
            </>
          ) : (
            <span className="dock-upload-inline__label">+ Drop PDF</span>
          )}
        </div>
        {uploadError && (
          <span className="dock-upload-inline__error" role="alert">
            {uploadError}
          </span>
        )}
        {mutationError && <span className="dock-upload-inline__error">{mutationError}</span>}
      </div>
    )
  }

  return (
    <div className="workflow-panel__upload workflow-panel__upload--inline">
      <div
        {...getRootProps()}
        className={`dropzone dropzone--compact mt-2 cursor-pointer px-4 py-5 text-center ${
          isDragActive ? 'dropzone--active' : ''
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-[var(--text)]">
          {isDragActive ? 'Release to dock…' : 'Drop PDFs here'}
        </p>
        <p className="mt-1 text-xs text-[var(--muted)]">
          {extensionHint(channel)} · confirm to dock
        </p>
      </div>

      {queuedFiles.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-xs text-[var(--muted)]">
          {queuedFiles.map((f) => (
            <li key={f.name}>{f.name}</li>
          ))}
        </ul>
      )}

      <div className="mt-2 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onConfirm}
          disabled={queuedFiles.length === 0 || isPending}
          className={`px-4 py-2 text-sm font-medium disabled:opacity-50 ${
            queuedFiles.length > 0 ? 'btn-primary' : 'btn-secondary'
          }`}
        >
          {isPending ? 'Uploading…' : 'Confirm upload'}
        </button>
      </div>

      {uploadError && (
        <p className="upload-error" role="alert">
          {uploadError}
        </p>
      )}

      {mutationError && <p className="mt-2 text-xs text-red-400">{mutationError}</p>}
      {uploadedFiles.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-xs text-[var(--success)]">
          {uploadedFiles.slice(0, 5).map((f) => (
            <li key={`${f.channel}-${f.name}`}>✓ {f.name}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
