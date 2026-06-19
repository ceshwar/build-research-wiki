import { useCallback, useEffect, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  dockArtifacts,
  fetchChannels,
  fetchJob,
  fetchJobLogs,
  fetchVaults,
  startBuild,
  surfaceInterval,
} from './api/client'
import type { Channel, Vault } from './types'

function Stat({
  label,
  value,
  highlight,
}: {
  label: string
  value: string | number
  highlight?: boolean
}) {
  return (
    <div
      className={`rounded-lg border px-4 py-3 ${
        highlight
          ? 'border-amber-600/50 bg-amber-950/20'
          : 'border-slate-700 bg-slate-800/50'
      }`}
    >
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${highlight ? 'text-amber-300' : 'text-white'}`}>
        {value}
      </div>
    </div>
  )
}

function statusColor(status: string) {
  switch (status) {
    case 'running':
    case 'queued':
      return 'text-amber-400'
    case 'completed':
      return 'text-emerald-400'
    case 'failed':
      return 'text-red-400'
    default:
      return 'text-slate-400'
  }
}

export default function App() {
  const queryClient = useQueryClient()
  const [vaultId, setVaultId] = useState('demo')
  const [channelId, setChannelId] = useState('my-portfolio')
  const [queuedFiles, setQueuedFiles] = useState<File[]>([])
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; channel: string }[]>([])

  const { data: vaults = [], isLoading: vaultsLoading } = useQuery<Vault[]>({
    queryKey: ['vaults'],
    queryFn: fetchVaults,
  })

  const { data: channels = [] } = useQuery<Channel[]>({
    queryKey: ['channels'],
    queryFn: fetchChannels,
  })

  const vault = vaults.find((v) => v.id === vaultId)
  const channel = channels.find((c) => c.id === channelId)
  const channelStats = vault?.channels.find((c) => c.id === channelId)
  const hasReef = vault ? vault.paper_count > 0 || !!vault.last_build : false
  const isPortfolio = channel?.profile === 'portfolio'

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
    }
  }, [jobQuery.data?.status, logsQuery.data?.status, queryClient])

  const dockMutation = useMutation({
    mutationFn: () => dockArtifacts(vaultId, queuedFiles, channelId),
    onSuccess: (data) => {
      setUploadedFiles((prev) => [
        ...data.filenames.map((f) => ({ name: f, channel: data.channel_name })),
        ...prev,
      ])
      setQueuedFiles([])
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
    },
  })

  const surfaceMutation = useMutation({
    mutationFn: () => surfaceInterval(vaultId, channelId, 'auto'),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  const rebuildMutation = useMutation({
    mutationFn: () => startBuild(vaultId, 'full'),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length) setQueuedFiles((prev) => [...prev, ...accepted])
  }, [])

  const acceptMap: Record<string, Record<string, string[]>> = {
    'my-portfolio': { 'application/pdf': ['.pdf'] },
    'lab-portfolio': { 'application/pdf': ['.pdf'] },
    'lit-review': { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'text/markdown': ['.md'] },
    'lab-memory': { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'text/markdown': ['.md'] },
    ideas: { 'text/plain': ['.txt'], 'text/markdown': ['.md'] },
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptMap[channelId] ?? { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'] },
    multiple: true,
  })

  const jobStatus = jobQuery.data?.status ?? logsQuery.data?.status
  const isDiving = jobStatus === 'running' || jobStatus === 'queued'

  if (vaultsLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-400">
        Descending…
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-cyan-400/80">
            SCUBA Lab
          </p>
          <h1 className="text-2xl font-bold text-white">SCUBA Ideaverse</h1>
          <p className="mt-1 text-sm text-slate-400">
            Your research world, mapped and connected.
          </p>
        </div>
        <select
          value={vaultId}
          onChange={(e) => {
            setVaultId(e.target.value)
            setQueuedFiles([])
            setUploadedFiles([])
            setActiveJobId(null)
          }}
          className="rounded-lg border border-slate-600 bg-slate-800 px-4 py-2 text-sm text-white"
        >
          {vaults.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
        </select>
      </header>

      {/* Dive Computer */}
      {vault && (
        <section className="mb-8">
          <h2 className="mb-3 text-xs font-medium uppercase tracking-widest text-slate-500">
            Dive Computer
          </h2>
          <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
            <Stat label="On chart" value={vault.on_chart ?? vault.paper_count} />
            <Stat
              label="Processed"
              value={vault.processed_count ?? 0}
              highlight={(vault.processed_count ?? 0) > 0}
            />
            <Stat
              label="Needs review"
              value={vault.needs_review_count ?? 0}
              highlight={(vault.needs_review_count ?? 0) > 0}
            />
            <Stat
              label="Pending surface"
              value={vault.pending_artifacts}
              highlight={vault.pending_artifacts > 0}
            />
            <Stat
              label="Last surface"
              value={vault.last_build ? vault.last_build.replace('T', ' ') : '—'}
            />
          </div>
          {(vault.needs_review_count ?? 0) > 0 && (
            <p className="mb-3 text-xs text-slate-500">
              <span className="text-amber-400">Needs review</span> = on chart but missing themes,
              abstract, or deep dive. <span className="text-emerald-400">Processed</span> = fully
              charted (like your fleshed-out paper pages).
            </p>
          )}

          <div className="grid gap-2 sm:grid-cols-2">
            {vault.channels.map((ch) => (
              <button
                key={ch.id}
                type="button"
                onClick={() => setChannelId(ch.id)}
                className={`rounded-lg border px-4 py-3 text-left transition-colors ${
                  channelId === ch.id
                    ? 'border-cyan-600/60 bg-cyan-950/30'
                    : 'border-slate-700 bg-slate-800/30 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white">{ch.name}</span>
                  <span className="text-xs text-slate-500">{ch.artifact_count} files</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">{ch.description}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  {(ch.processed ?? 0) > 0 && (
                    <span className="text-emerald-400">{ch.processed} processed</span>
                  )}
                  {(ch.needs_review ?? 0) > 0 && (
                    <span className="text-amber-400">{ch.needs_review} need review</span>
                  )}
                  {ch.pending > 0 && (
                    <span className="text-amber-400">{ch.pending} pending surface</span>
                  )}
                  {(ch.on_chart ?? 0) > 0 &&
                    !(ch.needs_review ?? 0) &&
                    !(ch.processed ?? 0) && (
                      <span className="text-slate-500">{ch.on_chart} on chart</span>
                    )}
                </div>
                {ch.needs_attention && ch.needs_attention.length > 0 && channelId === ch.id && (
                  <ul className="mt-2 space-y-0.5 text-xs text-amber-300/90">
                    {ch.needs_attention.slice(0, 4).map((item) => (
                      <li key={item.slug}>
                        ◦ {item.title}{' '}
                        <span className="text-slate-500">({item.status})</span>
                      </li>
                    ))}
                  </ul>
                )}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Dock */}
      <section className="mb-6">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-xs font-medium uppercase tracking-widest text-slate-500">
            Dock — {channel?.name ?? 'Channel'}
          </h2>
          <span className="text-xs text-slate-600">
            → <code className="text-slate-500">{channel?.raw_path}</code>
          </span>
        </div>

        <div
          {...getRootProps()}
          className={`cursor-pointer rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
            isDragActive
              ? 'border-cyan-400 bg-cyan-950/30'
              : 'border-slate-600 bg-slate-800/30 hover:border-slate-500'
          }`}
        >
          <input {...getInputProps()} />
          <p className="text-lg text-slate-200">
            {isDragActive ? 'Release into dock…' : 'Drop artifacts here'}
          </p>
          <p className="mt-2 text-sm text-slate-500">
            Staged until you confirm · {channel?.extensions.join(', ')}
          </p>
        </div>

        {queuedFiles.length > 0 && (
          <ul className="mt-4 space-y-1 text-sm text-slate-300">
            {queuedFiles.map((f) => (
              <li key={f.name}>◦ {f.name} (staged)</li>
            ))}
          </ul>
        )}

        <div className="mt-4">
          <button
            onClick={() => dockMutation.mutate()}
            disabled={queuedFiles.length === 0 || dockMutation.isPending}
            className="rounded-lg border border-cyan-700 bg-cyan-950/40 px-5 py-2.5 text-sm font-medium text-cyan-100 hover:bg-cyan-900/40 disabled:opacity-50"
          >
            {dockMutation.isPending ? 'Transferring…' : 'Confirm Upload'}
          </button>
        </div>

        {dockMutation.isError && (
          <p className="mt-2 text-sm text-red-400">{dockMutation.error.message}</p>
        )}

        {uploadedFiles.length > 0 && (
          <ul className="mt-4 space-y-1 text-sm text-emerald-400">
            {uploadedFiles.map((f) => (
              <li key={`${f.channel}-${f.name}`}>
                ✓ {f.name} → {f.channel}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Surface interval */}
      <section className="mb-8">
        <h2 className="mb-3 text-xs font-medium uppercase tracking-widest text-slate-500">
          Chart — {channel?.name}
        </h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => surfaceMutation.mutate()}
            disabled={surfaceMutation.isPending || isDiving}
            className="rounded-lg bg-violet-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50"
          >
            {surfaceMutation.isPending || isDiving
              ? 'Diving…'
              : 'Surface Interval — Update Chart'}
          </button>
          {isPortfolio && hasReef && (
            <button
              onClick={() => rebuildMutation.mutate()}
              disabled={rebuildMutation.isPending || isDiving}
              className="rounded-lg border border-slate-600 px-5 py-2.5 text-sm text-slate-300 hover:border-slate-500 disabled:opacity-50"
            >
              Full rebuild
            </button>
          )}
          {vault && (
            <a
              href={`obsidian://open?path=${encodeURIComponent(vault.path)}`}
              className="rounded-lg border border-slate-600 px-5 py-2.5 text-sm text-slate-300 hover:border-slate-500"
            >
              Open reef in Obsidian
            </a>
          )}
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Scaffolds chart entries from templates in <code className="text-slate-400">builder/entries/</code>
          {' '}— uploads stay in <code className="text-slate-400">raw/</code> only.
          {isPortfolio
            ? ' Updates papers, themes, concepts, and index.md.'
            : ' Updates wiki/sources shells; LLM Deep Dive fills generative sections later.'}
          {channelStats && channelStats.pending > 0 && (
            <span className="text-amber-400"> · {channelStats.pending} pending</span>
          )}
        </p>
        {(surfaceMutation.isError || rebuildMutation.isError) && (
          <p className="mt-2 text-sm text-red-400">
            {(surfaceMutation.error ?? rebuildMutation.error)?.message}
          </p>
        )}
      </section>

      {activeJobId && (
        <section className="rounded-xl border border-slate-700 bg-slate-900/80">
          <div className="flex items-center justify-between border-b border-slate-700 px-4 py-3">
            <span className="text-sm font-medium text-slate-200">Dive log</span>
            {jobStatus && (
              <span className={`text-sm font-medium uppercase ${statusColor(jobStatus)}`}>
                {jobStatus}
              </span>
            )}
          </div>
          <pre className="max-h-72 overflow-auto p-4 font-mono text-xs leading-relaxed text-slate-300">
            {(logsQuery.data?.lines ?? []).join('\n') || 'Waiting for output…'}
          </pre>
        </section>
      )}

      {vault && (
        <p className="mt-6 text-xs text-slate-600">
          Reef path: <code className="text-slate-500">{vault.path}</code>
        </p>
      )}
    </div>
  )
}
