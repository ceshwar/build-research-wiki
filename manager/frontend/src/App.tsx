import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  addVault,
  createDock,
  dockArtifacts,
  fetchChannels,
  fetchJob,
  fetchJobLogs,
  fetchVaults,
  pickVaultFolder,
  removeVault,
  startBuild,
  surfaceInterval,
  validateVaultPath,
} from './api/client'
import type { Channel, Vault } from './types'
import type { VaultValidateResult } from './api/client'

const MIME: Record<string, string> = {
  pdf: 'application/pdf',
  md: 'text/markdown',
  txt: 'text/plain',
}

function formatChartUpdated(iso: string | null | undefined) {
  if (!iso) return 'Never'
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function acceptForChannel(channel?: Channel) {
  if (!channel) return { 'application/pdf': ['.pdf'] }
  const map: Record<string, string[]> = {}
  for (const ext of channel.extensions) {
    const mime = MIME[ext] ?? 'application/octet-stream'
    map[mime] = [...(map[mime] ?? []), `.${ext}`]
  }
  return map
}

function SectionLabel({ children }: { children: ReactNode }) {
  return <h2 className="section-label">{children}</h2>
}

function Stat({
  label,
  hint,
  value,
  highlight,
}: {
  label: string
  hint?: string
  value: string | number
  highlight?: boolean
}) {
  return (
    <div className={`stat-card ${highlight ? 'stat-card--active' : ''}`}>
      <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--muted)]">
        {label}
      </div>
      {hint && <div className="mt-0.5 text-[10px] leading-snug text-[var(--muted)]">{hint}</div>}
      <div
        className={`mt-1.5 text-xl font-semibold tabular-nums ${
          highlight ? 'text-[var(--accent)]' : 'text-[var(--text)]'
        }`}
      >
        {value}
      </div>
    </div>
  )
}

function statusColor(status: string) {
  switch (status) {
    case 'running':
    case 'queued':
      return 'text-[var(--accent)]'
    case 'completed':
      return 'text-[var(--success)]'
    case 'failed':
      return 'text-red-400'
    default:
      return 'text-[var(--muted)]'
  }
}

export default function App() {
  const queryClient = useQueryClient()
  const [vaultId, setVaultId] = useState('demo')
  const [channelId, setChannelId] = useState('my-portfolio')
  const [queuedFiles, setQueuedFiles] = useState<File[]>([])
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; channel: string }[]>([])
  const [showAddReef, setShowAddReef] = useState(false)
  const [showAddDock, setShowAddDock] = useState(false)
  const [reefPath, setReefPath] = useState('')
  const [reefName, setReefName] = useState('')
  const [reefPreview, setReefPreview] = useState<VaultValidateResult | null>(null)
  const [dockName, setDockName] = useState('')
  const [dockEmoji, setDockEmoji] = useState('📁')

  const { data: vaults = [], isLoading: vaultsLoading } = useQuery<Vault[]>({
    queryKey: ['vaults'],
    queryFn: fetchVaults,
  })

  const { data: channels = [] } = useQuery<Channel[]>({
    queryKey: ['channels', vaultId],
    queryFn: () => fetchChannels(vaultId),
    enabled: !!vaultId,
  })

  const vault = vaults.find((v) => v.id === vaultId)
  const channel = channels.find((c) => c.id === channelId)
  const channelStats = vault?.channels.find((c) => c.id === channelId)
  const hasReef = vault ? vault.paper_count > 0 || !!vault.last_build : false
  const isPortfolio = channel?.profile === 'portfolio'

  useEffect(() => {
    if (channels.length && !channels.find((c) => c.id === channelId)) {
      setChannelId(channels[0].id)
    }
  }, [channels, channelId])

  const jobQuery = useQuery({
    queryKey: ['job', activeJobId],
    queryFn: () => fetchJob(activeJobId!),
    enabled: !!activeJobId,
    retry: false,
    refetchInterval: (q) => {
      const status = q.state.data?.status
      return status === 'running' || status === 'queued' ? 800 : false
    },
  })

  const logsQuery = useQuery({
    queryKey: ['job-logs', activeJobId],
    queryFn: () => fetchJobLogs(activeJobId!),
    enabled: !!activeJobId,
    retry: false,
    refetchInterval: (q) => {
      const status = jobQuery.data?.status ?? q.state.data?.status
      return status === 'running' || status === 'queued' ? 800 : false
    },
  })

  useEffect(() => {
    if (jobQuery.isError && activeJobId) setActiveJobId(null)
  }, [jobQuery.isError, activeJobId])

  useEffect(() => {
    const status = jobQuery.data?.status ?? logsQuery.data?.status
    if (status === 'completed' || status === 'failed') {
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      queryClient.invalidateQueries({ queryKey: ['channels'] })
    }
  }, [jobQuery.data?.status, logsQuery.data?.status, queryClient])

  const surfaceMutation = useMutation({
    mutationFn: () => surfaceInterval(vaultId, channelId, 'auto'),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  const dockMutation = useMutation({
    mutationFn: () => dockArtifacts(vaultId, queuedFiles, channelId),
    onSuccess: (data) => {
      setUploadedFiles((prev) => [
        ...data.filenames.map((f) => ({ name: f, channel: data.channel_name })),
        ...prev,
      ])
      setQueuedFiles([])
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      if (isPortfolio && data.files_added > 0) {
        surfaceMutation.mutate()
      }
    },
  })

  const rebuildMutation = useMutation({
    mutationFn: () => startBuild(vaultId, 'full'),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  const addDockMutation = useMutation({
    mutationFn: () => createDock(vaultId, { name: dockName.trim(), emoji: dockEmoji }),
    onSuccess: (dock) => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      setChannelId(dock.id)
      setShowAddDock(false)
      setDockName('')
      setDockEmoji('📁')
    },
  })

  const pickFolderMutation = useMutation({
    mutationFn: pickVaultFolder,
    onSuccess: async (data) => {
      if (data.cancelled || !data.path) return
      setReefPath(data.path)
      const preview = await validateVaultPath(data.path)
      setReefPreview(preview)
      if (preview.suggested_name) {
        setReefName((prev) => prev || preview.suggested_name)
      }
    },
  })

  const validateMutation = useMutation({
    mutationFn: () => validateVaultPath(reefPath),
    onSuccess: (data) => {
      setReefPreview(data)
      if (data.suggested_name && !reefName) setReefName(data.suggested_name)
    },
  })

  const addVaultMutation = useMutation({
    mutationFn: () => addVault(reefPath, reefName || undefined),
    onSuccess: (v) => {
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      setVaultId(v.id)
      setShowAddReef(false)
      setReefPath('')
      setReefName('')
      setReefPreview(null)
    },
  })

  const removeVaultMutation = useMutation({
    mutationFn: () => removeVault(vaultId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      setVaultId('demo')
    },
  })

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length) setQueuedFiles((prev) => [...prev, ...accepted])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptForChannel(channel),
    multiple: true,
  })

  const jobStatus = jobQuery.data?.status ?? logsQuery.data?.status
  const isDiving = jobStatus === 'running' || jobStatus === 'queued'
  const enrichCount =
    (vault?.needs_deep_dive_count ?? 0) + (vault?.needs_review_count ?? 0)

  if (vaultsLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-[var(--muted)]">
        Loading…
      </div>
    )
  }

  return (
    <>
      <header className="site-header">
        <div className="site-header__inner">
          <div className="site-header__brand">
            <div className="logo-wrap">
              <img src="/scuba-logo.png" alt="SCUBA Lab" width={40} height={40} />
            </div>
            <div>
              <h1>SCUBA Ideaverse</h1>
              <p className="tagline">Your research world, mapped and connected.</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={vaultId}
              onChange={(e) => {
                setVaultId(e.target.value)
                setQueuedFiles([])
                setUploadedFiles([])
                setActiveJobId(null)
              }}
            >
            {vaults.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
                {v.user_added ? ' ★' : ''}
              </option>
            ))}
            </select>
            <button
              type="button"
              onClick={() => setShowAddReef((s) => !s)}
              className="header-btn"
            >
              {showAddReef ? 'Cancel' : '+ Reef'}
            </button>
          </div>
        </div>
      </header>

      <div className="main-content">

      {showAddReef && (
        <section className="panel-card panel-card--accent mb-6">
          <SectionLabel>Add reef</SectionLabel>
          <p className="mb-3 text-xs text-[var(--muted)]">
            Point SCUBA at an existing Obsidian vault on this machine.
          </p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              type="text"
              value={reefPath}
              onChange={(e) => {
                setReefPath(e.target.value)
                setReefPreview(null)
              }}
              placeholder="/Users/you/Desktop/my-wiki"
              className="min-w-0 flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm text-[var(--text)] placeholder:text-[var(--muted)]"
            />
            <button
              type="button"
              onClick={() => pickFolderMutation.mutate()}
              disabled={pickFolderMutation.isPending}
              className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text)] hover:border-[var(--border-accent)] disabled:opacity-50"
            >
              Browse…
            </button>
          </div>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center">
            <input
              type="text"
              value={reefName}
              onChange={(e) => setReefName(e.target.value)}
              placeholder="Display name"
              className="min-w-0 flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={() => validateMutation.mutate()}
              disabled={!reefPath.trim() || validateMutation.isPending}
              className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm disabled:opacity-50"
            >
              Check
            </button>
            <button
              type="button"
              onClick={() => addVaultMutation.mutate()}
              disabled={!reefPreview?.ok || addVaultMutation.isPending}
              className="btn-primary px-4 py-2 text-sm disabled:opacity-50"
            >
              Add
            </button>
          </div>
          {reefPreview && (
            <p className={`mt-2 text-xs ${reefPreview.ok ? 'text-[var(--success)]' : 'text-red-400'}`}>
              {reefPreview.ok ? `✓ ${reefPreview.paper_count} papers` : reefPreview.error}
            </p>
          )}
        </section>
      )}

      {vault?.user_added && (
        <div className="panel-card mb-5 flex items-center justify-between px-3 py-2 text-xs text-[var(--muted)]">
          <span className="truncate" title={vault.path}>{vault.path}</span>
          <button
            type="button"
            onClick={() => removeVaultMutation.mutate()}
            className="ml-2 shrink-0 hover:text-red-400"
          >
            Remove
          </button>
        </div>
      )}

      {/* Dive Computer */}
      {vault && (
        <section className="mb-6">
          <div className="mb-3 flex items-baseline justify-between gap-2">
            <SectionLabel>Dive Computer</SectionLabel>
            <span className="text-[11px] text-[var(--muted)]">
              Chart updated {formatChartUpdated(vault.last_build)}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            <Stat label="On chart" hint="Artifacts on your wiki" value={vault.on_chart ?? vault.paper_count} />
            <Stat
              label="Awaiting chart"
              hint="Uploaded, not charted yet"
              value={vault.pending_artifacts}
              highlight={vault.pending_artifacts > 0}
            />
            <Stat
              label="Quick dip"
              hint="PDF facts only"
              value={vault.quick_dip_count ?? 0}
              highlight={(vault.quick_dip_count ?? 0) > 0}
            />
            <Stat
              label="Enrich next"
              hint="On chart — needs Deep Dive"
              value={enrichCount}
              highlight={enrichCount > 0}
            />
          </div>
        </section>
      )}

      {/* Dock picker */}
      <section className="mb-5">
        <div className="mb-2">
          <SectionLabel>Docks</SectionLabel>
        </div>
        <div className="flex flex-wrap gap-2">
          {channels.map((ch) => {
            const stats = vault?.channels.find((c) => c.id === ch.id)
            const count = stats?.artifact_count ?? 0
            const awaiting = stats?.pending ?? 0
            return (
              <button
                key={ch.id}
                type="button"
                onClick={() => setChannelId(ch.id)}
                className={`dock-pill ${channelId === ch.id ? 'dock-pill--active' : ''}`}
                title={
                  awaiting > 0
                    ? `${count} file${count === 1 ? '' : 's'} · ${awaiting} awaiting chart`
                    : `${count} file${count === 1 ? '' : 's'} in ${ch.raw_path}/`
                }
              >
                <span className="dock-pill__label text-sm font-medium text-[var(--text)]">
                  {ch.emoji} {ch.name}
                </span>
                <span className="dock-pill__count">{count}</span>
              </button>
            )
          })}
          <button
            type="button"
            onClick={() => setShowAddDock(true)}
            className="dock-pill text-[var(--muted)]"
          >
            + Add dock
          </button>
        </div>
        {channel && (
          <p className="mt-2 text-xs text-[var(--muted)]">
            {channel.description} · <code className="text-[var(--muted)]">{channel.raw_path}/</code>
          </p>
        )}
      </section>

      {showAddDock && (
        <section className="panel-card mb-5">
          <SectionLabel>New dock</SectionLabel>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Creates a folder under <code>raw/</code> in your vault and wires it into the chart pipeline.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <input
              value={dockEmoji}
              onChange={(e) => setDockEmoji(e.target.value)}
              className="w-14 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-2 py-2 text-center text-lg"
              maxLength={4}
            />
            <input
              value={dockName}
              onChange={(e) => setDockName(e.target.value)}
              placeholder="Dock name"
              className="min-w-[12rem] flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={() => addDockMutation.mutate()}
              disabled={!dockName.trim() || addDockMutation.isPending}
              className="btn-primary px-4 py-2 text-sm disabled:opacity-50"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setShowAddDock(false)}
              className="btn-secondary px-4 py-2 text-sm text-[var(--muted)]"
            >
              Cancel
            </button>
          </div>
          {addDockMutation.isError && (
            <p className="mt-2 text-xs text-red-400">{addDockMutation.error.message}</p>
          )}
        </section>
      )}

      {/* Upload */}
      <section className="mb-6">
        <SectionLabel>
          Upload to {channel?.emoji} {channel?.name}
        </SectionLabel>
        <div
          {...getRootProps()}
          className={`dropzone cursor-pointer px-6 py-8 text-center ${isDragActive ? 'dropzone--active' : ''}`}
        >
          <input {...getInputProps()} />
          <p className="text-[var(--text)]">
            {isDragActive ? 'Release to dock…' : 'Drop files here'}
          </p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            {channel?.extensions.map((e) => `.${e}`).join(', ')} · staged until you confirm
          </p>
        </div>

        {queuedFiles.length > 0 && (
          <ul className="mt-3 space-y-0.5 text-xs text-[var(--muted)]">
            {queuedFiles.map((f) => (
              <li key={f.name}>{f.name}</li>
            ))}
          </ul>
        )}

        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => dockMutation.mutate()}
            disabled={queuedFiles.length === 0 || dockMutation.isPending}
            className="btn-secondary px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {dockMutation.isPending ? 'Uploading…' : 'Confirm upload'}
          </button>
        </div>

        {dockMutation.isError && (
          <p className="mt-2 text-xs text-red-400">{dockMutation.error.message}</p>
        )}
        {uploadedFiles.length > 0 && (
          <ul className="mt-2 space-y-0.5 text-xs text-[var(--success)]">
            {uploadedFiles.slice(0, 5).map((f) => (
              <li key={`${f.channel}-${f.name}`}>✓ {f.name}</li>
            ))}
          </ul>
        )}
      </section>

      {/* Chart */}
      <section className="mb-6">
        <SectionLabel>Chart</SectionLabel>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => surfaceMutation.mutate()}
            disabled={surfaceMutation.isPending || isDiving}
            className="btn-primary px-4 py-2 text-sm disabled:opacity-50"
          >
            {surfaceMutation.isPending || isDiving ? 'Quick dip…' : 'Update chart'}
          </button>
          {isPortfolio && hasReef && (
            <button
              onClick={() => rebuildMutation.mutate()}
              disabled={rebuildMutation.isPending || isDiving}
              className="btn-secondary px-4 py-2 text-sm disabled:opacity-50"
            >
              Full rebuild
            </button>
          )}
          {vault && (
            <a
              href={`obsidian://open?path=${encodeURIComponent(vault.path)}`}
              className="btn-secondary px-4 py-2 text-sm link-accent"
            >
              Open in Obsidian
            </a>
          )}
        </div>
        <p className="mt-2 text-xs text-[var(--muted)]">
          Quick Dip pulls PDF facts onto your wiki chart. Deep Dive (in Obsidian) adds themes and analysis.
          {isPortfolio && ' Portfolio uploads run Quick Dip automatically.'}
        </p>
        {(surfaceMutation.isError || rebuildMutation.isError) && (
          <p className="mt-2 text-xs text-red-400">
            {(surfaceMutation.error ?? rebuildMutation.error)?.message}
          </p>
        )}
      </section>

      {activeJobId && (
        <section className="panel-card">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-3 py-2">
            <span className="text-xs font-medium text-[var(--text)]">Job log</span>
            {jobStatus && (
              <span className={`text-xs font-medium uppercase ${statusColor(jobStatus)}`}>
                {jobStatus}
              </span>
            )}
          </div>
          <pre className="max-h-48 overflow-auto p-3 font-mono text-[11px] leading-relaxed text-[var(--muted)]">
            {(logsQuery.data?.lines ?? []).join('\n') || 'Waiting…'}
          </pre>
        </section>
      )}

      {channelStats?.needs_attention && channelStats.needs_attention.length > 0 && (
        <section className="panel-card mt-4">
          <h3 className="text-xs font-medium text-[var(--text)]">Needs attention in this dock</h3>
          <ul className="mt-1.5 space-y-0.5 text-xs text-[var(--muted)]">
            {channelStats.needs_attention.slice(0, 4).map((item) => (
              <li key={item.slug}>
                {item.title}{' '}
                <span className="text-[var(--accent)]">({item.status.replace(/_/g, ' ')})</span>
              </li>
            ))}
          </ul>
        </section>
      )}
      </div>

      <footer className="site-footer">
        <div className="site-footer__inner">
          <div className="site-footer__brand">
            <img src="/scuba-logo.png" alt="" width={24} height={24} />
            <span>
              A product of{' '}
              <a href="https://eshwarchandrasekharan.com/lab.html" target="_blank" rel="noreferrer">
                SCUBA Lab
              </a>
              {' '}@ UIUC
            </span>
          </div>
          <span>
            <a
              href="https://github.com/ceshwar/build-research-wiki/blob/main/LICENSE"
              target="_blank"
              rel="noreferrer"
            >
              MIT License
            </a>
            {' '}· © 2026 Eshwar Chandrasekharan
          </span>
        </div>
      </footer>
    </>
  )
}
