import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  addVault,
  createDock,
  dockArtifacts,
  fetchChannels,
  fetchChartMap,
  fetchIngestPrompt,
  fetchJob,
  fetchJobLogs,
  fetchVaults,
  pickVaultFolder,
  removeVault,
  startBuild,
  surfaceInterval,
  validateVaultPath,
} from './api/client'
import type { Channel, ChartEntry, ChartMap, Vault } from './types'
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

function chartStatusPill(status: string) {
  switch (status) {
    case 'processed':
      return { icon: '📄', label: 'Deep dive', className: 'status-pill status-pill--done' }
    case 'quick_dip':
      return { icon: '🤿', label: 'Quick dip', className: 'status-pill status-pill--quick' }
    case 'needs_deep_dive':
      return { icon: '✎', label: 'Enrich next', className: 'status-pill status-pill--enrich' }
    case 'charted':
      return { icon: '📝', label: 'Charted', className: 'status-pill status-pill--quick' }
    default:
      return { icon: '○', label: status.replace(/_/g, ' '), className: 'status-pill' }
  }
}

function groupEntriesByTheme(map: ChartMap | undefined) {
  if (!map) return []
  const themeTitle = new Map(map.themes.map((t) => [t.slug, t.title]))
  const buckets = new Map<string, { slug: string; title: string; entries: ChartEntry[] }>()

  for (const t of map.themes) {
    buckets.set(t.slug, { slug: t.slug, title: t.title, entries: [] })
  }
  const unassigned: ChartEntry[] = []

  for (const entry of map.entries) {
    const themes = entry.themes.length ? entry.themes : []
    if (!themes.length) {
      unassigned.push(entry)
      continue
    }
    for (const slug of themes) {
      const bucket = buckets.get(slug)
      if (bucket) bucket.entries.push(entry)
      else {
        buckets.set(slug, {
          slug,
          title: themeTitle.get(slug) ?? slug,
          entries: [entry],
        })
      }
    }
  }

  const groups = [...buckets.values()].filter((g) => g.entries.length > 0)
  groups.sort((a, b) => b.entries.length - a.entries.length || a.title.localeCompare(b.title))
  if (unassigned.length) {
    groups.push({ slug: '_unassigned', title: 'Awaiting themes', entries: unassigned })
  }
  return groups
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
  const [ingestPrompt, setIngestPrompt] = useState<string | null>(null)
  const [promptCopied, setPromptCopied] = useState(false)

  const { data: vaults = [], isLoading: vaultsLoading } = useQuery<Vault[]>({
    queryKey: ['vaults'],
    queryFn: fetchVaults,
  })

  const { data: channels = [] } = useQuery<Channel[]>({
    queryKey: ['channels', vaultId],
    queryFn: () => fetchChannels(vaultId),
    enabled: !!vaultId,
  })

  const { data: chartMap, isLoading: chartMapLoading } = useQuery<ChartMap>({
    queryKey: ['chart-map', vaultId, channelId],
    queryFn: () => fetchChartMap(vaultId, channelId),
    enabled: !!vaultId && !!channelId,
  })

  const vault = vaults.find((v) => v.id === vaultId)
  const channel = channels.find((c) => c.id === channelId)
  const channelStats = vault?.channels.find((c) => c.id === channelId)
  const hasReef = vault ? vault.paper_count > 0 || !!vault.last_build : false
  const isPortfolio = channel?.profile === 'portfolio'
  const chartSupport = channel?.chart_support ?? (isPortfolio ? 'full' : 'preview')
  const isIngestPreview = chartSupport === 'preview'

  useEffect(() => {
    if (channels.length && !channels.find((c) => c.id === channelId)) {
      setChannelId(channels[0].id)
    }
  }, [channels, channelId])

  // The ingest prompt is per vault+dock; clear it when either changes.
  useEffect(() => {
    setIngestPrompt(null)
    setPromptCopied(false)
  }, [vaultId, channelId])

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
      queryClient.invalidateQueries({ queryKey: ['chart-map'] })
    }
  }, [jobQuery.data?.status, logsQuery.data?.status, queryClient])

  const surfaceMutation = useMutation({
    mutationFn: () => surfaceInterval(vaultId, channelId, 'auto'),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  const handleUpdateChart = useCallback(() => {
    if (isIngestPreview) {
      const ok = window.confirm(
        'Full ingest for this dock is in development (Phase 3).\n\n' +
          'Update chart will only create a thin Quick Dip placeholder shell in wiki/sources/ — ' +
          'not a finished source page with summaries, takeaways, and entity links.\n\n' +
          'Your files stay safe in raw/. Continue with placeholder shell?'
      )
      if (!ok) return
    }
    surfaceMutation.mutate()
  }, [isIngestPreview, surfaceMutation])

  const dockMutation = useMutation({
    mutationFn: () => dockArtifacts(vaultId, queuedFiles, channelId),
    onSuccess: (data) => {
      setUploadedFiles((prev) => [
        ...data.filenames.map((f) => ({ name: f, channel: data.channel_name })),
        ...prev,
      ])
      setQueuedFiles([])
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      queryClient.invalidateQueries({ queryKey: ['chart-map'] })
      if (isPortfolio && data.files_added > 0) {
        surfaceMutation.mutate()
      }
    },
  })

  const rebuildMutation = useMutation({
    mutationFn: () => startBuild(vaultId, 'full'),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  const ingestPromptMutation = useMutation({
    mutationFn: () => fetchIngestPrompt(vaultId, channelId),
    onSuccess: (data) => {
      setIngestPrompt(data.prompt)
      setPromptCopied(false)
    },
  })

  const copyPrompt = useCallback(() => {
    if (!ingestPrompt) return
    navigator.clipboard.writeText(ingestPrompt).then(() => {
      setPromptCopied(true)
      setTimeout(() => setPromptCopied(false), 2000)
    })
  }, [ingestPrompt])

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
  const themeGroups = groupEntriesByTheme(chartMap)
  const chartedFileSet = new Set(
    (chartMap?.entries ?? []).map((e) => e.pdf).filter(Boolean),
  )

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
        {isIngestPreview && (
          <div className="notice-callout mt-3">
            <strong>In development.</strong> You can dock files here — they land in{' '}
            <code>{channel?.raw_path}/</code> and stay safe. Full LLM ingest (faithful summaries,
            entity links, takeaways) ships in Phase 3. Until then, <strong>Update chart</strong>{' '}
            only creates a thin placeholder shell, not a finished source page.
          </div>
        )}
      </section>

      {/* Portfolio / channel map */}
      <section className="mb-6">
        <SectionLabel>
          {isPortfolio ? 'Portfolio map' : `${channel?.emoji ?? ''} ${channel?.name ?? 'Dock'} map`}
        </SectionLabel>
        {chartMapLoading && (
          <p className="text-xs text-[var(--muted)]">Loading chart…</p>
        )}
        {chartMap && (
          <div className="chart-map">
            <div className="panel-card">
              <h3 className="text-xs font-semibold text-[var(--text)]">
                Files in {channel?.raw_path ?? 'dock'}/
              </h3>
              <p className="mt-1 text-[11px] text-[var(--muted)]">
                {chartMap.raw_files.length} file{chartMap.raw_files.length === 1 ? '' : 's'} docked
                {chartMap.awaiting_chart.length > 0 &&
                  ` · ${chartMap.awaiting_chart.length} awaiting chart`}
              </p>
              {chartMap.raw_files.length > 0 ? (
                <div className="chart-map__files mt-2">
                  {chartMap.raw_files.map((f) => (
                    <span
                      key={f}
                      className={`chart-file ${
                        chartMap.awaiting_chart.includes(f) || !chartedFileSet.has(f)
                          ? 'chart-file--awaiting'
                          : ''
                      }`}
                      title={
                        chartMap.awaiting_chart.includes(f)
                          ? 'Uploaded — run Update chart'
                          : chartedFileSet.has(f)
                            ? 'On chart'
                            : 'In dock'
                      }
                    >
                      {f}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-xs text-[var(--muted)]">No files docked yet.</p>
              )}
            </div>

            {chartMap.entries.length > 0 && (
              <div className="panel-card overflow-x-auto">
                <h3 className="text-xs font-semibold text-[var(--text)]">On chart</h3>
                <p className="mt-1 text-[11px] text-[var(--muted)]">
                  {chartMap.entries.length} paper{chartMap.entries.length === 1 ? '' : 's'} mapped
                  to wiki pages
                </p>
                <table className="chart-table mt-3">
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Paper</th>
                      <th>Themes</th>
                      <th>File</th>
                    </tr>
                  </thead>
                  <tbody>
                    {chartMap.entries.map((entry) => {
                      const pill = chartStatusPill(entry.status)
                      return (
                        <tr key={entry.slug}>
                          <td>
                            <span className={pill.className}>
                              {pill.icon} {pill.label}
                            </span>
                          </td>
                          <td>
                            <div className="font-medium text-[var(--text)]">{entry.title}</div>
                            {(entry.year || entry.venue) && (
                              <div className="text-[11px] text-[var(--muted)]">
                                {[entry.year, entry.venue].filter(Boolean).join(' · ')}
                              </div>
                            )}
                            <div className="text-[10px] text-[var(--muted)]">{entry.wiki_page}</div>
                          </td>
                          <td>
                            {entry.themes.length ? (
                              entry.themes.map((t) => (
                                <span key={t} className="theme-chip">
                                  {t}
                                </span>
                              ))
                            ) : (
                              <span className="text-[11px] text-[var(--muted)]">—</span>
                            )}
                          </td>
                          <td className="text-[11px] text-[var(--muted)]">{entry.pdf || '—'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {isPortfolio && themeGroups.length > 0 && (
              <div className="panel-card">
                <h3 className="text-xs font-semibold text-[var(--text)]">By theme</h3>
                <p className="mt-1 text-[11px] text-[var(--muted)]">
                  Papers grouped by research theme — your portfolio landscape at a glance.
                </p>
                <div className="theme-map mt-3">
                  {themeGroups.map((group) => (
                    <div
                      key={group.slug}
                      className={`theme-map__card ${
                        group.slug === '_unassigned' ? 'theme-map__card--unassigned' : ''
                      }`}
                    >
                      <div className="theme-map__title">{group.title}</div>
                      {group.entries.map((entry) => {
                        const pill = chartStatusPill(entry.status)
                        return (
                          <div key={`${group.slug}-${entry.slug}`} className="theme-map__paper">
                            <span>{pill.icon}</span>
                            <span>{entry.title}</span>
                          </div>
                        )
                      })}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
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
            {isIngestPreview && ' · full ingest coming in Phase 3'}
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
        {isIngestPreview && (
          <div className="notice-callout mb-3">
            <strong>Preview only.</strong> Chart update for {channel?.emoji} {channel?.name} is not
            production-ready. Use <strong>⚓ My Portfolio</strong> for full Quick Dip charting today,
            or dock here and wait for Phase 3 ingest.
          </div>
        )}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleUpdateChart}
            disabled={surfaceMutation.isPending || isDiving}
            className="btn-primary px-4 py-2 text-sm disabled:opacity-50"
          >
            {surfaceMutation.isPending || isDiving
              ? 'Updating…'
              : isIngestPreview
                ? 'Update chart (preview)'
                : 'Update chart'}
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
          {isIngestPreview ? (
            <>
              Placeholder shells land in <code>wiki/sources/</code>. Phase 3 will add full LLM
              ingest (summary, takeaways, entities).
            </>
          ) : (
            <>
              Quick Dip pulls PDF facts onto your wiki chart. Deep Dive (in Obsidian) adds themes
              and analysis.
              {isPortfolio && ' Portfolio uploads run Quick Dip automatically.'}
            </>
          )}
        </p>
        {(surfaceMutation.isError || rebuildMutation.isError) && (
          <p className="mt-2 text-xs text-red-400">
            {(surfaceMutation.error ?? rebuildMutation.error)?.message}
          </p>
        )}
      </section>

      {/* Manual-agent ingest — paste-ready prompt for the user's own coding agent */}
      <section className="mb-6">
        <SectionLabel>Deep Dive with your agent</SectionLabel>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Quick Dip pulls the facts; the enrichment — themes, one-liners, deep dives — is done by
          your own coding agent. Generate a ready-to-paste prompt for {channel?.emoji}{' '}
          {channel?.name}, open this vault in Claude Code or Cursor, and paste it.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => ingestPromptMutation.mutate()}
            disabled={ingestPromptMutation.isPending}
            className="btn-secondary px-4 py-2 text-sm disabled:opacity-50"
          >
            {ingestPromptMutation.isPending ? 'Generating…' : 'Get ingest prompt'}
          </button>
          {ingestPrompt && (
            <button onClick={copyPrompt} className="btn-secondary px-4 py-2 text-sm">
              {promptCopied ? 'Copied ✓' : 'Copy prompt'}
            </button>
          )}
        </div>
        {ingestPrompt && (
          <pre className="panel-card mt-3 max-h-72 overflow-auto whitespace-pre-wrap p-3 font-mono text-[11px] leading-relaxed text-[var(--muted)]">
            {ingestPrompt}
          </pre>
        )}
        {ingestPromptMutation.isError && (
          <p className="mt-2 text-xs text-red-400">{ingestPromptMutation.error.message}</p>
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
