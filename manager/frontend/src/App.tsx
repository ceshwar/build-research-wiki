import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useDropzone, type FileRejection } from 'react-dropzone'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { HowToPanel } from './components/HowToPanel'
import { ChartGraphView } from './components/ChartGraphView'
import { ContentDrawer } from './components/ContentDrawer'
import { QueryPanel } from './components/QueryPanel'
import { SettingsPanel } from './components/SettingsPanel'
import {
  addVault,
  createDock,
  dockArtifacts,
  fetchChannels,
  fetchChartGraph,
  fetchChartMap,
  fetchJob,
  fetchJobLogs,
  fetchSettings,
  fetchVaults,
  pickVaultFolder,
  removeFromChartBatch,
  removeVault,
  runDeepDive,
  startBuild,
  surfaceInterval,
  updateChartVerification,
  validateVaultPath,
} from './api/client'
import type { Channel, ChartEntry, ChartGraph, ChartMap, Vault } from './types'
import { enrichmentLabel, territoryLabel } from './lib/enrichment'
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

type StatFilter = 'all' | 'on_chart' | 'pending' | 'quick_dip' | 'enrich' | 'processed' | 'needs_deep_dive' | 'charted' | 'needs_verification' | 'uncharted'
type MapSortKey = 'status' | 'paper' | 'themes'
type MapSortDir = 'asc' | 'desc'

const MISSING_PAPER_YEAR = 1

const MAP_STATUS_CHIPS: { id: StatFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'processed', label: 'Deep dive' },
  { id: 'needs_verification', label: 'Needs review' },
  { id: 'uncharted', label: 'Uncharted' },
  { id: 'quick_dip', label: 'Quick dip' },
]

function dockPillTooltip(
  ch: { description: string; raw_path: string },
  count: number,
  awaiting: number,
): string {
  const files =
    awaiting > 0
      ? `${count} file${count === 1 ? '' : 's'} · ${awaiting} awaiting chart`
      : `${count} file${count === 1 ? '' : 's'} in ${ch.raw_path}/`
  return `${ch.description} — ${files}`
}

function PipelineLegend() {
  return (
    <div className="pipeline-strip" role="note" aria-label="Chart pipeline">
      <span className="pipeline-strip__step">Dock PDF</span>
      <span className="pipeline-strip__arrow">→</span>
      <span className="pipeline-strip__step">Quick Dip</span>
      <span className="pipeline-strip__arrow">→</span>
      <span className="pipeline-strip__step">Deep Dive (LLM)</span>
      <span className="pipeline-strip__arrow">→</span>
      <span className="pipeline-strip__step">Human review</span>
      <span className="pipeline-strip__arrow">→</span>
      <span className="pipeline-strip__step">Verified</span>
    </div>
  )
}

function Stat({
  label,
  hint,
  value,
  highlight,
  variant = 'chart',
  selected,
  onClick,
}: {
  label: string
  hint?: string
  value: string | number
  highlight?: boolean
  variant?: 'chart' | 'pending' | 'quick' | 'enrich' | 'verify'
  selected?: boolean
  onClick?: () => void
}) {
  const className = [
    'stat-card',
    `stat-card--${variant}`,
    onClick ? 'stat-card--clickable' : '',
    highlight ? 'stat-card--active' : '',
    selected ? 'stat-card--selected' : '',
  ]
    .filter(Boolean)
    .join(' ')

  const inner = (
    <>
      <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--muted)]">
        {label}
      </div>
      {hint && <div className="mt-0.5 text-[12px] leading-snug text-[var(--muted)]">{hint}</div>}
      <div
        className={`mt-1.5 text-xl font-semibold tabular-nums ${
          highlight || selected ? 'text-[var(--accent)]' : 'text-[var(--text)]'
        }`}
      >
        {value}
      </div>
    </>
  )

  if (onClick) {
    return (
      <button type="button" className={className} onClick={onClick}>
        {inner}
      </button>
    )
  }
  return <div className={className}>{inner}</div>
}

function filterChartEntries(entries: ChartEntry[], filter: StatFilter): ChartEntry[] {
  if (filter === 'all' || filter === 'on_chart') return entries
  if (filter === 'quick_dip') return entries.filter((e) => e.status === 'quick_dip')
  if (filter === 'processed') return entries.filter((e) => e.status === 'processed')
  if (filter === 'needs_deep_dive') return entries.filter((e) => e.status === 'needs_deep_dive')
  if (filter === 'charted') return entries.filter((e) => e.status === 'charted')
  if (filter === 'needs_verification') {
    return entries.filter((e) => e.needs_human_verification)
  }
  if (filter === 'uncharted') {
    return entries.filter((e) => e.territory === 'uncharted')
  }
  if (filter === 'enrich') {
    return entries.filter((e) => e.status === 'quick_dip' || e.status === 'needs_deep_dive')
  }
  return entries
}

function themeSortLabel(entry: ChartEntry, themes: { slug: string; title: string }[]) {
  if (!entry.themes.length) return '\uffff'
  return entry.themes
    .map((slug) => themes.find((t) => t.slug === slug)?.title ?? slug)
    .sort((a, b) => a.localeCompare(b))
    .join(', ')
}

function sortChartEntries(
  entries: ChartEntry[],
  key: MapSortKey,
  dir: MapSortDir,
  themes: { slug: string; title: string }[],
): ChartEntry[] {
  const mul = dir === 'asc' ? 1 : -1
  return [...entries].sort((a, b) => {
    let cmp = 0
    if (key === 'paper') {
      cmp = (a.year ?? MISSING_PAPER_YEAR) - (b.year ?? MISSING_PAPER_YEAR)
      if (cmp === 0) cmp = a.title.localeCompare(b.title, undefined, { sensitivity: 'base' })
    } else if (key === 'status') {
      cmp = chartStatusPill(a.status).label.localeCompare(chartStatusPill(b.status).label)
      if (cmp === 0) cmp = a.title.localeCompare(b.title, undefined, { sensitivity: 'base' })
    } else {
      cmp = themeSortLabel(a, themes).localeCompare(themeSortLabel(b, themes))
      if (cmp === 0) cmp = a.title.localeCompare(b.title, undefined, { sensitivity: 'base' })
    }
    return cmp * mul
  })
}

function SortableTh({
  label,
  sortKey,
  activeKey,
  dir,
  onSort,
}: {
  label: string
  sortKey: MapSortKey
  activeKey: MapSortKey
  dir: MapSortDir
  onSort: (key: MapSortKey) => void
}) {
  const active = activeKey === sortKey
  const arrow = active ? (dir === 'asc' ? ' ↑' : ' ↓') : ''
  return (
    <th>
      <button type="button" className="chart-table__sort" onClick={() => onSort(sortKey)}>
        {label}
        <span className="chart-table__sort-indicator" aria-hidden>
          {arrow}
        </span>
      </button>
    </th>
  )
}

function PathBreadcrumb({
  reefName,
  dock,
  onRootClick,
  onReefClick,
  meta,
}: {
  reefName: string
  dock?: { emoji: string; name: string }
  onRootClick?: () => void
  onReefClick?: () => void
  meta?: ReactNode
}) {
  return (
    <nav className="path-breadcrumb" aria-label="Current reef and dock">
      {onRootClick ? (
        <button
          type="button"
          className="path-breadcrumb__part path-breadcrumb__part--root path-breadcrumb__part--link"
          onClick={onRootClick}
          title="Switch reef"
        >
          /
        </button>
      ) : (
        <span className="path-breadcrumb__part path-breadcrumb__part--root">/</span>
      )}
      <span className="path-breadcrumb__sep" aria-hidden>
        ›
      </span>
      {onReefClick ? (
        <button
          type="button"
          className="path-breadcrumb__part path-breadcrumb__part--link"
          onClick={onReefClick}
          title="Choose dock"
        >
          {reefName}
        </button>
      ) : (
        <span className="path-breadcrumb__part">{reefName}</span>
      )}
      {dock && (
        <>
          <span className="path-breadcrumb__sep" aria-hidden>
            ›
          </span>
          <span className="path-breadcrumb__part path-breadcrumb__part--current">
            {dock.emoji} {dock.name}
          </span>
        </>
      )}
      {meta}
    </nav>
  )
}

function filterThemeGroups(
  groups: ReturnType<typeof groupEntriesByTheme>,
  filter: StatFilter,
): ReturnType<typeof groupEntriesByTheme> {
  if (filter === 'all' || filter === 'on_chart' || filter === 'pending') return groups
  return groups
    .map((g) => ({
      ...g,
      entries: filterChartEntries(g.entries, filter),
    }))
    .filter((g) => g.entries.length > 0)
}

type SectionId = 'section-docks' | 'section-dive' | 'section-map' | 'section-actions' | 'section-query'
type WorkspaceSectionId = 'section-dive' | 'section-map' | 'section-actions' | 'section-query'

const DOCK_WORKSPACE_SECTIONS: {
  id: WorkspaceSectionId
  label: string
  hint: string
  badge?: (ctx: { enrich: number; pending: number; needsVerification: number }) => number | null
}[] = [
  { id: 'section-map', label: 'Navigate', hint: 'Browse your chart' },
  {
    id: 'section-query',
    label: 'Query',
    hint: 'Ask the wiki',
  },
  {
    id: 'section-dive',
    label: 'Status',
    hint: 'Track progress',
    badge: (c) => c.needsVerification || c.enrich || null,
  },
  {
    id: 'section-actions',
    label: 'Actions',
    hint: 'Update & enrich',
    badge: (c) => (c.pending > 0 ? c.pending : c.enrich > 0 ? c.enrich : null),
  },
]

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
    case 'scaffolded':
      return { icon: '○', label: 'Scaffolded', className: 'status-pill status-pill--scaffold' }
    case 'charted':
      return { icon: '📝', label: 'Charted', className: 'status-pill status-pill--quick' }
    default:
      return { icon: '○', label: status.replace(/_/g, ' '), className: 'status-pill' }
  }
}

function verificationPill(entry: ChartEntry) {
  if (entry.human_verified) {
    return { icon: '✓', label: 'Verified', className: 'status-pill status-pill--verified' }
  }
  if (entry.needs_human_verification || entry.llm_enriched) {
    const src = enrichmentLabel(entry) || 'Needs review'
    return { icon: '⚠', label: src, className: 'status-pill status-pill--review' }
  }
  if (entry.territory === 'uncharted') {
    return { icon: '◇', label: territoryLabel('uncharted'), className: 'status-pill status-pill--uncharted' }
  }
  const src = enrichmentLabel(entry)
  if (src && src !== 'Quick dip') {
    return { icon: '·', label: src, className: 'status-pill status-pill--source' }
  }
  return null
}

function obsidianReefHref(
  reefPath: string,
  opts: { vaultPath: string; obsidianVaultId?: string | null },
) {
  const rel = reefPath.replace(/^\//, '')
  if (opts.obsidianVaultId) {
    return `obsidian://open?vault=${encodeURIComponent(opts.obsidianVaultId)}&file=${encodeURIComponent(rel)}`
  }
  const base = opts.vaultPath.replace(/\/$/, '')
  return `obsidian://open?path=${encodeURIComponent(`${base}/${rel}`)}`
}

function themeWikiPage(slug: string) {
  return `wiki/themes/${slug}.md`
}

const THEME_GRADIENT: Record<string, string> = {
  'digital-governance': 'theme-gradient--governance',
  'healthy-online-behavior': 'theme-gradient--behavior',
  'algorithmic-ai-audits': 'theme-gradient--audits',
  'computational-social-science': 'theme-gradient--csc',
  'social-media-online-communities': 'theme-gradient--communities',
}

function themeGradientClass(slug: string) {
  return THEME_GRADIENT[slug] ?? 'theme-gradient--default'
}

function themeDisplayTitle(slug: string, themes: { slug: string; title: string }[]) {
  return themes.find((t) => t.slug === slug)?.title ?? slug
}

function ReefLink({
  vaultPath,
  obsidianVaultId,
  reefPath,
  children,
  className = 'link-accent',
  viewIn = 'app',
  onOpenInApp,
}: {
  vaultPath?: string
  obsidianVaultId?: string | null
  reefPath?: string
  children: ReactNode
  className?: string
  viewIn?: 'app' | 'obsidian'
  onOpenInApp?: (path: string, title?: string) => void
}) {
  if (!vaultPath || !reefPath) {
    return <>{children}</>
  }
  if (viewIn === 'app' && onOpenInApp) {
    return (
      <button
        type="button"
        className={`${className} link-button`}
        title={`Open ${reefPath} in Portolan`}
        onClick={() => onOpenInApp(reefPath, typeof children === 'string' ? children : undefined)}
      >
        {children}
      </button>
    )
  }
  return (
    <a
      href={obsidianReefHref(reefPath, { vaultPath, obsidianVaultId })}
      className={className}
      title={`Open ${reefPath} in Obsidian`}
    >
      {children}
    </a>
  )
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

const CONNECT_REEF = '__connect__'

function dockGuideDismissedKey(vaultId: string) {
  return `scuba-dock-guide-dismissed:${vaultId}`
}

function dockSeenKey(vaultId: string, channelId: string) {
  return `scuba-dock-seen:${vaultId}:${channelId}`
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
  const [howToOpen, setHowToOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [viewer, setViewer] = useState<{ path: string; title?: string } | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [dockName, setDockName] = useState('')
  const [dockEmoji, setDockEmoji] = useState('📁')
  const [queryJobMeta, setQueryJobMeta] = useState<{ model: string; elapsed_s?: number } | null>(
    null,
  )
  const [statFilter, setStatFilter] = useState<StatFilter>('all')
  const [mapTab, setMapTab] = useState<'list' | 'theme' | 'graph'>('list')
  const [showBackToTop, setShowBackToTop] = useState(false)
  const [uploadExpanded, setUploadExpanded] = useState(false)
  const [showDockPicker, setShowDockPicker] = useState(false)
  const [showReefPicker, setShowReefPicker] = useState(false)
  const [activeWorkspaceSection, setActiveWorkspaceSection] =
    useState<WorkspaceSectionId>('section-map')
  const [dockGuideDismissed, setDockGuideDismissed] = useState(false)
  const [expandedPaperSlugs, setExpandedPaperSlugs] = useState<Set<string>>(() => new Set())
  const [mapEditMode, setMapEditMode] = useState(false)
  const [mapEditError, setMapEditError] = useState<string | null>(null)
  const [pendingRemovalSlugs, setPendingRemovalSlugs] = useState<Set<string>>(() => new Set())
  const [mapSort, setMapSort] = useState<{ key: MapSortKey; dir: MapSortDir }>({
    key: 'paper',
    dir: 'desc',
  })

  const { data: vaults = [], isLoading: vaultsLoading } = useQuery<Vault[]>({
    queryKey: ['vaults'],
    queryFn: fetchVaults,
  })

  const { data: appSettings } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  })
  const viewIn = appSettings?.view_in ?? 'app'

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

  const { data: chartGraph, isLoading: chartGraphLoading } = useQuery<ChartGraph>({
    queryKey: ['chart-graph', vaultId, channelId],
    queryFn: () => fetchChartGraph(vaultId, channelId),
    enabled: !!vaultId && !!channelId && isPortfolio,
  })

  useEffect(() => {
    if (channels.length && !channels.find((c) => c.id === channelId)) {
      setChannelId(channels[0].id)
    }
  }, [channels, channelId])

  useEffect(() => {
    setDockGuideDismissed(localStorage.getItem(dockGuideDismissedKey(vaultId)) === '1')
  }, [vaultId])

  // Reset workspace UI when reef or dock changes.
  useEffect(() => {
    setStatFilter('all')
    setUploadExpanded(false)
    setShowDockPicker(false)
    setShowReefPicker(false)
    setActiveWorkspaceSection('section-map')
    setExpandedPaperSlugs(new Set())
    setMapEditMode(false)
    setPendingRemovalSlugs(new Set())
  }, [vaultId, channelId])

  useEffect(() => {
    if (queuedFiles.length > 0) setUploadExpanded(true)
  }, [queuedFiles.length])

  useEffect(() => {
    const onScroll = () => setShowBackToTop(window.scrollY > 420)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    if (!howToOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setHowToOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [howToOpen])

  const openReefPicker = useCallback(() => {
    setShowReefPicker(true)
    setShowDockPicker(false)
    requestAnimationFrame(() => {
      document.getElementById('section-reefs')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }, [])

  const openDockPicker = useCallback((opts?: { expandUpload?: boolean }) => {
    setShowReefPicker(false)
    setShowDockPicker(true)
    if (opts?.expandUpload) setUploadExpanded(true)
    requestAnimationFrame(() => {
      document.getElementById('section-docks')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }, [])

  const scrollToSection = useCallback(
    (id: SectionId, opts?: { expandUpload?: boolean; expandActions?: boolean }) => {
      if (id === 'section-docks') {
        openDockPicker({ expandUpload: opts?.expandUpload })
        return
      }
      setShowDockPicker(false)
      setShowReefPicker(false)
      setUploadExpanded(false)
      if (id === 'section-dive' || id === 'section-map' || id === 'section-actions' || id === 'section-query') {
        setActiveWorkspaceSection(id)
      }
    },
    [openDockPicker],
  )

  const focusWorkspaceSection = useCallback((id: WorkspaceSectionId) => {
    setShowDockPicker(false)
    setShowReefPicker(false)
    setActiveWorkspaceSection(id)
  }, [])

  const dismissDockGuide = useCallback(() => {
    localStorage.setItem(dockGuideDismissedKey(vaultId), '1')
    setDockGuideDismissed(true)
  }, [vaultId])

  const selectDock = useCallback(
    (nextChannelId: string) => {
      const isFirstVisit = localStorage.getItem(dockSeenKey(vaultId, nextChannelId)) !== '1'
      setShowDockPicker(false)
      setChannelId(nextChannelId)
      setActiveWorkspaceSection('section-map')
      requestAnimationFrame(() => {
        if (isFirstVisit) {
          localStorage.setItem(dockSeenKey(vaultId, nextChannelId), '1')
        }
      })
    },
    [vaultId],
  )

  const toggleMapSort = useCallback((key: MapSortKey) => {
    setMapSort((prev) =>
      prev.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: key === 'paper' ? 'desc' : 'asc' },
    )
  }, [])

  const setMapStatusFilter = useCallback((filter: StatFilter) => {
    setStatFilter(filter)
    setMapTab('list')
    focusWorkspaceSection('section-map')
  }, [focusWorkspaceSection])

  const togglePaperExpand = useCallback((slug: string) => {
    setExpandedPaperSlugs((prev) => {
      const next = new Set(prev)
      if (next.has(slug)) next.delete(slug)
      else next.add(slug)
      return next
    })
  }, [])

  const toggleStatFilter = useCallback(
    (filter: StatFilter) => {
      const next = statFilter === filter ? 'all' : filter
      setStatFilter(next)
      setMapTab('list')
      focusWorkspaceSection('section-map')
    },
    [statFilter, focusWorkspaceSection],
  )

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
      queryClient.invalidateQueries({ queryKey: ['chart-graph'] })
    }
  }, [jobQuery.data?.status, logsQuery.data?.status, queryClient])

  const surfaceMutation = useMutation({
    mutationFn: () => surfaceInterval(vaultId, channelId, 'auto'),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  const removeFromChartMutation = useMutation({
    mutationFn: (slugs: string[]) => removeFromChartBatch(vaultId, channelId, slugs),
    onSuccess: (data) => {
      setMapEditError(null)
      setPendingRemovalSlugs(new Set())
      setMapEditMode(false)
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      queryClient.invalidateQueries({ queryKey: ['chart-map', vaultId, channelId] })
      queryClient.invalidateQueries({ queryKey: ['chart-graph', vaultId, channelId] })
      if (data.job_id) setActiveJobId(data.job_id)
    },
    onError: (err) => {
      setMapEditError(err instanceof Error ? err.message : 'Could not remove papers from chart.')
    },
  })

  const togglePendingRemoval = useCallback((slug: string) => {
    setPendingRemovalSlugs((prev) => {
      const next = new Set(prev)
      if (next.has(slug)) next.delete(slug)
      else next.add(slug)
      return next
    })
  }, [])

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
      setUploadError(null)
      setUploadExpanded(false)
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      queryClient.invalidateQueries({ queryKey: ['chart-map'] })
      queryClient.invalidateQueries({ queryKey: ['chart-graph'] })
      if (isPortfolio && data.files_added > 0) {
        surfaceMutation.mutate()
      }
    },
  })

  const rebuildMutation = useMutation({
    mutationFn: () => startBuild(vaultId, 'full'),
    onSuccess: (data) => setActiveJobId(data.job_id),
  })

  const verifyMutation = useMutation({
    mutationFn: ({ slug, verified }: { slug: string; verified: boolean }) =>
      updateChartVerification(vaultId, channelId, slug, verified),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['vaults'] })
      queryClient.invalidateQueries({ queryKey: ['chart-map', vaultId, channelId] })
      queryClient.invalidateQueries({ queryKey: ['chart-graph', vaultId, channelId] })
      if (data.job_id) setActiveJobId(data.job_id)
    },
  })

  const deepDiveMutation = useMutation({
    mutationFn: (opts: { slug?: string; slugs?: string[] }) =>
      runDeepDive(vaultId, channelId, opts),
    onSuccess: (data) => {
      setQueryJobMeta(null)
      setActiveJobId(data.job_id)
    },
  })

  const openInApp = useCallback(
    (path: string, title?: string) => {
      setViewer({ path, title })
    },
    [],
  )

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
    if (accepted.length) {
      setUploadError(null)
      setQueuedFiles((prev) => [...prev, ...accepted])
    }
  }, [])

  const onDropRejected = useCallback(
    (rejections: FileRejection[]) => {
      const extList = channel?.extensions.map((e) => `.${e}`).join(', ') ?? '.pdf'
      const msgs = rejections.map((r) => {
        const codes = r.errors.map((e) => e.code)
        if (codes.includes('file-invalid-type')) {
          return `${r.file.name} is not accepted for ${channel?.name ?? 'this dock'} — use ${extList}.`
        }
        return `${r.file.name}: ${r.errors[0]?.message ?? 'upload rejected'}`
      })
      setUploadError(msgs.join(' '))
      setUploadExpanded(true)
    },
    [channel],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected,
    accept: acceptForChannel(channel),
    multiple: true,
  })

  const jobStatus = jobQuery.data?.status ?? logsQuery.data?.status
  const isDiving = jobStatus === 'running' || jobStatus === 'queued'
  const enrichCount =
    (vault?.needs_deep_dive_count ?? 0) + (vault?.needs_review_count ?? 0)
  const needsVerificationCount =
    channelStats?.needs_human_verification ??
    vault?.needs_human_verification_count ??
    0
  const needsVerificationEntries =
    chartMap?.entries.filter((e) => e.needs_human_verification) ?? []
  const themeGroups = groupEntriesByTheme(chartMap)
  const filteredEntries = filterChartEntries(chartMap?.entries ?? [], statFilter)
  const sortedEntries = useMemo(
    () => sortChartEntries(filteredEntries, mapSort.key, mapSort.dir, chartMap?.themes ?? []),
    [filteredEntries, mapSort, chartMap?.themes],
  )

  const handleFinishMapEdit = useCallback(() => {
    if (pendingRemovalSlugs.size === 0) {
      setMapEditMode(false)
      return
    }
    const titles = sortedEntries
      .filter((e) => pendingRemovalSlugs.has(e.slug))
      .map((e) => e.title)
    const preview = titles.slice(0, 6)
    const more =
      titles.length > preview.length ? `\n…and ${titles.length - preview.length} more` : ''
    const ok = window.confirm(
      `Remove ${pendingRemovalSlugs.size} paper${pendingRemovalSlugs.size === 1 ? '' : 's'} from the chart?\n\n` +
        `${preview.map((t) => `• ${t}`).join('\n')}${more}\n\n` +
        'PDFs stay in the dock — you can chart them again with Update chart.',
    )
    if (!ok) return
    removeFromChartMutation.mutate([...pendingRemovalSlugs])
  }, [pendingRemovalSlugs, sortedEntries, removeFromChartMutation])

  const handleCancelMapEdit = useCallback(() => {
    if (pendingRemovalSlugs.size > 0) {
      const ok = window.confirm(
        `Discard ${pendingRemovalSlugs.size} pending removal${pendingRemovalSlugs.size === 1 ? '' : 's'}?`,
      )
      if (!ok) return
    }
    setPendingRemovalSlugs(new Set())
    setMapEditError(null)
    setMapEditMode(false)
  }, [pendingRemovalSlugs.size])

  const filteredThemeGroups = filterThemeGroups(themeGroups, statFilter)
  const enrichEntries =
    chartMap?.entries.filter(
      (e) => e.status === 'quick_dip' || e.status === 'needs_deep_dive',
    ) ?? []
  const pendingCount = chartMap?.awaiting_chart.length ?? vault?.pending_artifacts ?? 0
  const inWorkspace = !!(vault && channel && !showDockPicker && !showReefPicker)
  const builtinVaults = vaults.filter((v) => !v.user_added)
  const userVaults = vaults.filter((v) => v.user_added)

  const handleVaultSelect = useCallback(
    (nextId: string) => {
      if (nextId === CONNECT_REEF) {
        setShowReefPicker(false)
        setShowAddReef(true)
        return
      }
      setVaultId(nextId)
      setShowAddReef(false)
      setShowReefPicker(false)
      setShowDockPicker(true)
      setQueuedFiles([])
      setUploadedFiles([])
      setActiveJobId(null)
    },
    [],
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
      <header className="site-header site-header--minimal">
        <div className="site-header__inner site-header__inner--minimal">
          <button
            type="button"
            className="header-icon-btn header-docs-btn"
            onClick={() => setHowToOpen(true)}
            title="How to use Portolan"
          >
            Docs
          </button>
          <button
            type="button"
            className="header-icon-btn header-icon-btn--settings"
            onClick={() => setSettingsOpen(true)}
            title="Settings"
            aria-label="Settings"
          >
            ⚙
          </button>
        </div>
      </header>

      <div className="main-content">
      <div className="page-intro mb-6">
        <div className="page-intro__brand">
          <img src="/scuba-logo.png" alt="" width={36} height={36} />
          <div>
            <h1 className="page-intro__title">Portolan</h1>
            <p className="page-intro__tagline">Read what you dock. Chart the connections.</p>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Built for reading, in a world built for writing — stay oriented as the ocean of research keeps rising.
            </p>
          </div>
        </div>
      </div>

      {showAddReef && (
        <section className="panel-card panel-card--accent mb-6">
          <SectionLabel>Connect your reef</SectionLabel>
          <p className="mb-3 text-xs text-[var(--muted)]">
            Point Portolan at a reef already on this machine. Different from{' '}
            <strong>Shallow reef</strong> (demo) or <strong>Blank reef</strong> (repo scaffold) —
            you are registering <em>your</em> Obsidian folder.
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
              Connect
            </button>
            <button
              type="button"
              onClick={() => setShowAddReef(false)}
              className="btn-secondary px-4 py-2 text-sm text-[var(--muted)]"
            >
              Cancel
            </button>
          </div>
          {reefPreview && (
            <p className={`mt-2 text-xs ${reefPreview.ok ? 'text-[var(--success)]' : 'text-red-400'}`}>
              {reefPreview.ok ? `✓ ${reefPreview.paper_count} papers` : reefPreview.error}
            </p>
          )}
        </section>
      )}

      {vault?.user_added && !inWorkspace && (
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

      {/* Reef picker — switch reef or connect your own */}
      {showReefPicker && (
        <section id="section-reefs" className="workflow-panel mb-6 scroll-mt-4">
          <div className="workflow-panel__head">
            <nav className="path-breadcrumb" aria-label="Reef picker">
              <span className="path-breadcrumb__part path-breadcrumb__part--root path-breadcrumb__part--current">
                /
              </span>
              <span className="path-breadcrumb__sep" aria-hidden>
                ›
              </span>
              <span className="workflow-panel__head-hint">Choose a reef</span>
            </nav>
            {vault && channel && (
              <button
                type="button"
                className="icon-btn"
                onClick={() => setShowReefPicker(false)}
              >
                Back to workspace
              </button>
            )}
          </div>
          <div className="workflow-panel__docks">
            <SectionLabel>Reefs</SectionLabel>
            <div className="flex flex-wrap gap-2">
              {builtinVaults.map((v) => (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => handleVaultSelect(v.id)}
                  className={`reef-pill ${vaultId === v.id ? 'reef-pill--active' : ''}`}
                  title={v.id === 'demo' ? 'Demo portfolio — safe to explore' : 'Empty scaffold — copy or spawn your own'}
                >
                  {v.name}
                </button>
              ))}
              {userVaults.map((v) => (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => handleVaultSelect(v.id)}
                  className={`reef-pill ${vaultId === v.id ? 'reef-pill--active' : ''}`}
                  title={v.path}
                >
                  {v.name}
                </button>
              ))}
              <button
                type="button"
                onClick={() => handleVaultSelect(CONNECT_REEF)}
                className="reef-pill reef-pill--action"
              >
                + Connect your reef…
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Dock picker — switch dock or upload; hidden once a dock workspace is active */}
      {vault && showDockPicker && (
      <section id="section-docks" className="workflow-panel mb-6 scroll-mt-4">
        <div className="workflow-panel__head">
          <PathBreadcrumb
            reefName={vault.name}
            onRootClick={openReefPicker}
          />
          {channel && (
            <button type="button" className="icon-btn" onClick={() => setShowDockPicker(false)}>
              Back to workspace
            </button>
          )}
        </div>
        <div className="workflow-panel__docks">
          <SectionLabel>Docks</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {channels.map((ch) => {
              const stats = vault?.channels.find((c) => c.id === ch.id)
              const count = stats?.artifact_count ?? 0
              const awaiting = stats?.pending ?? 0
              return (
                <button
                  key={ch.id}
                  type="button"
                  onClick={() => selectDock(ch.id)}
                  className={`dock-pill ${channelId === ch.id ? 'dock-pill--active' : ''}`}
                  title={dockPillTooltip(ch, count, awaiting)}
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
          {isIngestPreview && (
            <div className="notice-callout mt-3">
              <strong>In development.</strong> Files dock safely in <code>{channel?.raw_path}/</code>.
              Full ingest ships in Phase 3 — <strong>Update chart</strong> creates placeholder shells only.
            </div>
          )}

          <div className="workflow-upload-bar mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              className={`text-sm ${uploadExpanded ? 'btn-secondary' : 'btn-primary'} px-3 py-1.5`}
              onClick={() => setUploadExpanded((e) => !e)}
            >
              {uploadExpanded
                ? 'Hide upload'
                : `Upload to ${channel?.emoji ?? ''} ${channel?.name ?? 'dock'}`}
            </button>
            {queuedFiles.length > 0 && (
              <span className="text-xs font-medium text-[var(--accent)]">
                {queuedFiles.length} file{queuedFiles.length === 1 ? '' : 's'} staged
              </span>
            )}
            {!uploadExpanded && pendingCount > 0 && (
              <span className="text-xs text-[var(--muted)]">
                {pendingCount} awaiting chart — upload or{' '}
                <button
                  type="button"
                  className="link-accent text-xs underline"
                  onClick={() => scrollToSection('section-actions')}
                >
                  update chart
                </button>
              </span>
            )}
          </div>

          {uploadExpanded && (
            <div className="workflow-panel__upload workflow-panel__upload--inline">
              <div
                {...getRootProps()}
                className={`dropzone dropzone--compact mt-2 cursor-pointer px-4 py-5 text-center ${isDragActive ? 'dropzone--active' : ''}`}
              >
                <input {...getInputProps()} />
                <p className="text-sm text-[var(--text)]">
                  {isDragActive ? 'Release to dock…' : 'Drop PDFs here'}
                </p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {channel?.extensions.map((e) => `.${e}`).join(', ')} · confirm to dock
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
                  onClick={() => dockMutation.mutate()}
                  disabled={queuedFiles.length === 0 || dockMutation.isPending}
                  className={`px-4 py-2 text-sm font-medium disabled:opacity-50 ${
                    queuedFiles.length > 0 ? 'btn-primary' : 'btn-secondary'
                  }`}
                >
                  {dockMutation.isPending ? 'Uploading…' : 'Confirm upload'}
                </button>
              </div>

              {uploadError && (
                <p className="upload-error" role="alert">
                  {uploadError}
                </p>
              )}

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
            </div>
          )}
        </div>
      </section>
      )}

      {showAddDock && (
        <section className="panel-card mb-5">
          <SectionLabel>New dock</SectionLabel>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Creates a folder under <code>raw/</code> in your reef and wires it into the chart pipeline.
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

      {inWorkspace && vault && channel && (
        <div className="workspace-shell">
          <div className="workspace-shell__header">
            <PathBreadcrumb
              reefName={vault.name}
              dock={{ emoji: channel.emoji, name: channel.name }}
              onRootClick={openReefPicker}
              onReefClick={() => openDockPicker()}
              meta={
                <span className="workspace-shell__meta">
                  {chartMap?.entries.length ?? channelStats?.on_chart ?? 0} on chart
                  {(channelStats?.pending ?? pendingCount) > 0 &&
                    ` · ${channelStats?.pending ?? pendingCount} awaiting`}
                </span>
              }
            />
            <div className="workspace-shell__tabs" role="tablist" aria-label="Dock workspace">
              {DOCK_WORKSPACE_SECTIONS.map((item) => {
                const badge = item.badge?.({
                  enrich: enrichEntries.length,
                  pending: pendingCount,
                  needsVerification: needsVerificationCount,
                })
                return (
                  <button
                    key={item.id}
                    type="button"
                    role="tab"
                    aria-selected={activeWorkspaceSection === item.id}
                    className={`workspace-shell__tab ${
                      activeWorkspaceSection === item.id ? 'workspace-shell__tab--active' : ''
                    }`}
                    title={item.hint}
                    onClick={() => focusWorkspaceSection(item.id)}
                  >
                    <span>{item.label}</span>
                    {badge != null && badge > 0 && (
                      <span className="workspace-shell__tab-badge">{badge}</span>
                    )}
                  </button>
                )
              })}
            </div>
            {!dockGuideDismissed && (
              <div className="workspace-shell__guide">
                <span>
                  <strong>Navigate</strong> browses your chart · <strong>Query</strong> asks the wiki ·{' '}
                  <strong>Status</strong> tracks pipeline · <strong>Actions</strong> runs Quick Dip and
                  LLM Deep Dive.
                </span>
                <button type="button" className="workspace-shell__guide-dismiss" onClick={dismissDockGuide}>
                  Got it
                </button>
              </div>
            )}
          </div>

          <div className="workspace-shell__body">
      {activeWorkspaceSection === 'section-map' && (
      <div id="section-map" className="workspace-panel">
        <div className="workspace-panel__toolbar">
          {statFilter !== 'all' && (
            <button type="button" className="icon-btn" onClick={() => setStatFilter('all')}>
              Clear filter
            </button>
          )}
          {chartMap && chartMap.entries.length > 0 ? (
            <div className="view-tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={mapTab === 'list'}
                className={`view-tabs__tab ${mapTab === 'list' ? 'view-tabs__tab--active' : ''}`}
                onClick={() => setMapTab('list')}
              >
                List
              </button>
              {isPortfolio && (
                <button
                  type="button"
                  role="tab"
                  aria-selected={mapTab === 'theme'}
                  className={`view-tabs__tab ${mapTab === 'theme' ? 'view-tabs__tab--active' : ''}`}
                  onClick={() => {
                    setMapTab('theme')
                    setMapEditMode(false)
                    setPendingRemovalSlugs(new Set())
                  }}
                >
                  By theme
                </button>
              )}
              {isPortfolio && (
                <button
                  type="button"
                  role="tab"
                  aria-selected={mapTab === 'graph'}
                  className={`view-tabs__tab ${mapTab === 'graph' ? 'view-tabs__tab--active' : ''}`}
                  onClick={() => {
                    setMapTab('graph')
                    setMapEditMode(false)
                    setPendingRemovalSlugs(new Set())
                  }}
                >
                  Graph
                </button>
              )}
            </div>
          ) : null}
        </div>
          <div className="workspace-panel__content">
            {chartMapLoading && (
              <p className="text-sm text-[var(--muted)]">Loading chart…</p>
            )}
            {chartMap && statFilter === 'pending' && pendingCount > 0 && (
              <div className="empty-map">
                <p>
                  {pendingCount} file{pendingCount === 1 ? '' : 's'} in{' '}
                  <ReefLink vaultPath={vault?.path}
                    obsidianVaultId={vault?.obsidian_vault_id} reefPath={chartMap.raw_path} className="link-accent">
                    {chartMap.raw_path}/
                  </ReefLink>{' '}
                  awaiting chart.
                </p>
                <button
                  type="button"
                  className="btn-primary mt-3 px-4 py-2 text-sm"
                  onClick={() => scrollToSection('section-actions')}
                >
                  Update chart
                </button>
              </div>
            )}
            {chartMap && chartMap.entries.length === 0 && statFilter !== 'pending' && (
              <div className="empty-map">
                <p>No papers on chart yet. Upload PDFs to this dock, then run Update chart.</p>
                <button
                  type="button"
                  className="btn-secondary mt-3 px-4 py-2 text-sm"
                  onClick={() => scrollToSection('section-docks', { expandUpload: true })}
                >
                  Go to upload
                </button>
              </div>
            )}
            {chartMap && chartMap.entries.length > 0 && statFilter !== 'pending' && (
              <>
                {mapTab === 'list' && (
                  <>
                    <div className="map-toolbar">
                      <div className="map-status-filters" role="group" aria-label="Filter by status">
                        {MAP_STATUS_CHIPS.map((chip) => (
                          <button
                            key={chip.id}
                            type="button"
                            className={`map-status-chip ${
                              statFilter === chip.id ? 'map-status-chip--active' : ''
                            }`}
                            aria-pressed={statFilter === chip.id}
                            onClick={() =>
                              setMapStatusFilter(statFilter === chip.id ? 'all' : chip.id)
                            }
                          >
                            {chip.label}
                          </button>
                        ))}
                      </div>
                      {!mapEditMode ? (
                        <button
                          type="button"
                          className="map-edit-toggle"
                          onClick={() => {
                            setMapEditError(null)
                            setMapEditMode(true)
                          }}
                        >
                          Edit
                        </button>
                      ) : (
                        <div className="map-edit-actions">
                          <button
                            type="button"
                            className="map-edit-cancel"
                            onClick={handleCancelMapEdit}
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            className="map-edit-done"
                            disabled={removeFromChartMutation.isPending}
                            onClick={handleFinishMapEdit}
                          >
                            {pendingRemovalSlugs.size > 0
                              ? `Done · remove ${pendingRemovalSlugs.size}`
                              : 'Done'}
                          </button>
                        </div>
                      )}
                    </div>
                    {mapEditMode && (
                      <p className="map-edit-hint">
                        Mark papers with <span aria-hidden="true">−</span> to remove, then click{' '}
                        <strong>Done</strong>. PDFs stay in the dock.
                      </p>
                    )}
                    {mapEditError && (
                      <p className="map-edit-error" role="alert">
                        {mapEditError}
                      </p>
                    )}
                  <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
                    {sortedEntries.length === 0 ? (
                      <div className="empty-map">No papers match this filter.</div>
                    ) : (
                      <table
                        className={`chart-table${mapEditMode ? ' chart-table--edit' : ''}`}
                      >
                        <thead>
                          <tr>
                            {mapEditMode && (
                              <th className="chart-table__action-col" aria-hidden="true" />
                            )}
                            <SortableTh
                              label="Status"
                              sortKey="status"
                              activeKey={mapSort.key}
                              dir={mapSort.dir}
                              onSort={toggleMapSort}
                            />
                            <SortableTh
                              label="Paper"
                              sortKey="paper"
                              activeKey={mapSort.key}
                              dir={mapSort.dir}
                              onSort={toggleMapSort}
                            />
                            <SortableTh
                              label="Themes"
                              sortKey="themes"
                              activeKey={mapSort.key}
                              dir={mapSort.dir}
                              onSort={toggleMapSort}
                            />
                          </tr>
                        </thead>
                        <tbody>
                          {sortedEntries.map((entry) => {
                            const pill = chartStatusPill(entry.status)
                            const expanded = expandedPaperSlugs.has(entry.slug)
                            const canExpand = !!(entry.overview?.trim() || entry.pdf_path)
                            const marked = pendingRemovalSlugs.has(entry.slug)
                            return (
                              <tr
                                key={entry.slug}
                                className={`chart-table__row${marked ? ' chart-table__row--marked' : ''}`}
                              >
                                {mapEditMode && (
                                  <td className="chart-table__action-col">
                                    <button
                                      type="button"
                                      className={`chart-table__remove${marked ? ' chart-table__remove--marked' : ''}`}
                                      disabled={removeFromChartMutation.isPending}
                                      aria-label={
                                        marked
                                          ? `Undo remove ${entry.title}`
                                          : `Mark ${entry.title} for removal`
                                      }
                                      aria-pressed={marked}
                                      title={marked ? 'Undo' : 'Mark for removal'}
                                      onClick={() => togglePendingRemoval(entry.slug)}
                                    >
                                      −
                                    </button>
                                  </td>
                                )}
                                <td>
                                  <div className="flex flex-wrap items-center gap-1">
                                    <span className={pill.className}>
                                      {pill.icon} {pill.label}
                                    </span>
                                    {(() => {
                                      const vp = verificationPill(entry)
                                      return vp ? (
                                        <span className={vp.className} title={entry.llm_model || undefined}>
                                          {vp.icon} {vp.label}
                                        </span>
                                      ) : null
                                    })()}
                                  </div>
                                </td>
                                <td>
                                  <div className="map-paper-cell">
                                    <div className="font-medium text-[var(--text)]">
                                      <ReefLink
                                        vaultPath={vault?.path}
                                        obsidianVaultId={vault?.obsidian_vault_id}
                                        reefPath={entry.wiki_page}
                                        viewIn={viewIn}
                                        onOpenInApp={openInApp}
                                        className="link-accent"
                                      >
                                        {entry.title}
                                      </ReefLink>
                                    </div>
                                    <div className="paper-meta text-[12px] text-[var(--muted)]">
                                      {[entry.year, entry.venue].filter(Boolean).join(' · ')}
                                      {canExpand && (
                                        <>
                                          {(entry.year || entry.venue) && ' · '}
                                          <button
                                            type="button"
                                            className="map-paper-toggle"
                                            aria-expanded={expanded}
                                            onClick={() => togglePaperExpand(entry.slug)}
                                          >
                                            {expanded ? 'Hide note' : 'Note'}
                                          </button>
                                        </>
                                      )}
                                    </div>
                                    {expanded && (
                                      <div className="map-paper-detail">
                                        {entry.overview?.trim() ? (
                                          <p className="map-paper-overview">{entry.overview}</p>
                                        ) : (
                                          <p className="map-paper-overview map-paper-overview--empty">
                                            No overview yet — run Deep Dive to add a one-liner.
                                          </p>
                                        )}
                                        {entry.pdf_path && (
                                          <ReefLink
                                            vaultPath={vault?.path}
                                            obsidianVaultId={vault?.obsidian_vault_id}
                                            reefPath={entry.pdf_path}
                                            viewIn={viewIn}
                                            onOpenInApp={openInApp}
                                            className="map-paper-pdf-link"
                                          >
                                            View PDF
                                          </ReefLink>
                                        )}
                                        {entry.needs_human_verification && (
                                          <button
                                            type="button"
                                            className="btn-secondary mt-2 px-2 py-1 text-xs"
                                            disabled={verifyMutation.isPending}
                                            onClick={() =>
                                              verifyMutation.mutate({ slug: entry.slug, verified: true })
                                            }
                                          >
                                            Mark human verified
                                          </button>
                                        )}
                                        {entry.human_verified && entry.llm_enriched && (
                                          <p className="mt-2 text-xs text-[var(--success)]">
                                            Verified
                                            {entry.verified_by ? ` by ${entry.verified_by}` : ''}
                                            {entry.verified_at ? ` · ${entry.verified_at}` : ''}
                                          </p>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </td>
                                <td>
                                  {entry.themes.length ? (
                                    entry.themes.map((t) => (
                                      <ReefLink
                                        key={t}
                                        vaultPath={vault?.path}
                                        obsidianVaultId={vault?.obsidian_vault_id}
                                        reefPath={themeWikiPage(t)}
                                        viewIn={viewIn}
                                        onOpenInApp={openInApp}
                                        className={`theme-chip ${themeGradientClass(t)}`}
                                      >
                                        {themeDisplayTitle(t, chartMap.themes)}
                                      </ReefLink>
                                    ))
                                  ) : (
                                    <span className="text-[12px] text-[var(--muted)]">—</span>
                                  )}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    )}
                  </div>
                  </>
                )}

                {mapTab === 'theme' && isPortfolio && (
                  <div className="theme-map">
                    {filteredThemeGroups.length === 0 ? (
                      <div className="empty-map col-span-full">No papers match this filter.</div>
                    ) : (
                      filteredThemeGroups.map((group) => (
                        <div
                          key={group.slug}
                          className={`theme-map__card ${themeGradientClass(group.slug)} ${
                            group.slug === '_unassigned' ? 'theme-map__card--unassigned' : ''
                          }`}
                        >
                          <div className="theme-map__title">
                            {group.slug === '_unassigned' ? (
                              group.title
                            ) : (
                              <ReefLink
                                vaultPath={vault?.path}
                                obsidianVaultId={vault?.obsidian_vault_id}
                                reefPath={themeWikiPage(group.slug)}
                                viewIn={viewIn}
                                onOpenInApp={openInApp}
                                className="theme-map__title-link"
                              >
                                {group.title}
                              </ReefLink>
                            )}
                            <span className="ml-1 text-[10px] font-normal text-[var(--muted)]">
                              · {group.entries.length}
                            </span>
                          </div>
                          {group.entries.map((entry) => {
                            const pill = chartStatusPill(entry.status)
                            const vp = verificationPill(entry)
                            return (
                              <div key={`${group.slug}-${entry.slug}`} className="theme-map__paper">
                                <span>
                                  {pill.icon}
                                  {vp ? vp.icon : ''}
                                </span>
                                <ReefLink
                                  vaultPath={vault?.path}
                                  obsidianVaultId={vault?.obsidian_vault_id}
                                  reefPath={entry.wiki_page}
                                  viewIn={viewIn}
                                  onOpenInApp={openInApp}
                                  className="link-accent theme-map__paper-link"
                                >
                                  {entry.title}
                                </ReefLink>
                              </div>
                            )
                          })}
                        </div>
                      ))
                    )}
                  </div>
                )}
                {mapTab === 'graph' && isPortfolio && vault?.path && (
                  <>
                    <div className="map-toolbar">
                      <div className="map-status-filters" role="group" aria-label="Filter by status">
                        {MAP_STATUS_CHIPS.map((chip) => (
                          <button
                            key={chip.id}
                            type="button"
                            className={`map-status-chip ${
                              statFilter === chip.id ? 'map-status-chip--active' : ''
                            }`}
                            aria-pressed={statFilter === chip.id}
                            onClick={() =>
                              setMapStatusFilter(statFilter === chip.id ? 'all' : chip.id)
                            }
                          >
                            {chip.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    <ChartGraphView
                      active
                      graph={chartGraph}
                      loading={chartGraphLoading}
                      vaultPath={vault.path}
                      obsidianVaultId={vault.obsidian_vault_id}
                      statFilter={statFilter}
                      onOpenPage={viewIn === 'app' ? openInApp : undefined}
                    />
                  </>
                )}
              </>
            )}
          </div>
      </div>
      )}

      {activeWorkspaceSection === 'section-dive' && (
      <div id="section-dive" className="workspace-panel">
        <p className="workspace-panel__meta">
          Chart updated {formatChartUpdated(vault.last_build)}
        </p>
        <div className="workspace-panel__content">
              <PipelineLegend />

              <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-5">
                <Stat
                  label="On chart"
                  hint="Click to show all"
                  variant="chart"
                  value={vault.on_chart ?? vault.paper_count}
                  selected={statFilter === 'on_chart'}
                  onClick={() => toggleStatFilter('on_chart')}
                />
                <Stat
                  label="Awaiting chart"
                  hint="Docked, not mapped"
                  variant="pending"
                  value={pendingCount}
                  highlight={pendingCount > 0}
                  selected={statFilter === 'pending'}
                  onClick={() => toggleStatFilter('pending')}
                />
                <Stat
                  label="Quick dip"
                  hint="PDF facts only"
                  variant="quick"
                  value={vault.quick_dip_count ?? 0}
                  highlight={(vault.quick_dip_count ?? 0) > 0}
                  selected={statFilter === 'quick_dip'}
                  onClick={() => toggleStatFilter('quick_dip')}
                />
                <Stat
                  label="Enrich next"
                  hint="Needs Deep Dive"
                  variant="enrich"
                  value={enrichEntries.length || enrichCount}
                  highlight={enrichEntries.length > 0 || enrichCount > 0}
                  selected={statFilter === 'enrich'}
                  onClick={() => toggleStatFilter('enrich')}
                />
                <Stat
                  label="Needs review"
                  hint="LLM Deep Dive — not verified"
                  variant="verify"
                  value={needsVerificationCount}
                  highlight={needsVerificationCount > 0}
                  selected={statFilter === 'needs_verification'}
                  onClick={() => toggleStatFilter('needs_verification')}
                />
              </div>

              {enrichEntries.length > 0 && (
                <div className="next-step-banner mt-4">
                  <div>
                    <strong>
                      {enrichEntries.length} paper{enrichEntries.length === 1 ? '' : 's'} need Deep Dive
                    </strong>
                    <p>
                      Run LLM Deep Dive in Actions to add themes, one-liners, and analysis (
                      {appSettings?.llm.models.deep_dive ?? 'qwen3:32b'}).
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => focusWorkspaceSection('section-actions')}
                    className="btn-primary px-4 py-2 text-sm"
                  >
                    Go to Actions
                  </button>
                </div>
              )}

              {needsVerificationEntries.length > 0 && (
                <div className="next-step-banner mt-4 next-step-banner--review">
                  <div>
                    <strong>
                      {needsVerificationEntries.length} paper
                      {needsVerificationEntries.length === 1 ? '' : 's'} need human review
                    </strong>
                    <p>
                      LLM Deep Dive ({needsVerificationEntries[0]?.llm_model || 'qwen3:32b'}) fills
                      content but does not certify accuracy — review claims, then mark verified.
                    </p>
                  </div>
                </div>
              )}

              {(channelStats?.needs_verification?.length ?? 0) > 0 && (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
                    Awaiting verification
                  </h3>
                  <ul className="needs-list mt-1">
                    {channelStats!.needs_verification!.map((item) => (
                      <li key={item.slug} className="flex flex-wrap items-center gap-2">
                        <ReefLink
                          vaultPath={vault?.path}
                          obsidianVaultId={vault?.obsidian_vault_id}
                          reefPath={
                            isPortfolio
                              ? `wiki/papers/${item.slug}.md`
                              : `wiki/sources/${item.slug}.md`
                          }
                          viewIn={viewIn}
                          onOpenInApp={openInApp}
                          className="link-accent"
                        >
                          {item.title}
                        </ReefLink>
                        {item.llm_model && (
                          <span className="text-[var(--muted)] text-xs">({item.llm_model})</span>
                        )}
                        <button
                          type="button"
                          className="btn-secondary px-2 py-0.5 text-xs"
                          disabled={verifyMutation.isPending}
                          onClick={() => verifyMutation.mutate({ slug: item.slug, verified: true })}
                        >
                          Mark verified
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {channelStats?.needs_attention && channelStats.needs_attention.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
                    Needs attention
                  </h3>
                  <ul className="needs-list mt-1">
                    {channelStats.needs_attention.map((item) => (
                      <li key={item.slug}>
                        <ReefLink
                          vaultPath={vault?.path}
                          obsidianVaultId={vault?.obsidian_vault_id}
                          reefPath={
                            isPortfolio
                              ? `wiki/papers/${item.slug}.md`
                              : `wiki/sources/${item.slug}.md`
                          }
                          viewIn={viewIn}
                          onOpenInApp={openInApp}
                          className="link-accent"
                        >
                          {item.title}
                        </ReefLink>{' '}
                        <span className="text-[var(--accent)] text-xs">
                          ({item.status.replace(/_/g, ' ')})
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
        </div>
      </div>
      )}

      {activeWorkspaceSection === 'section-actions' && (
      <div id="section-actions" className="workspace-panel">
        <div className="workspace-panel__content">
            <div className="workspace-panel__upload-hint">
              <button
                type="button"
                className="btn-secondary px-3 py-1.5 text-sm"
                onClick={() => openDockPicker({ expandUpload: true })}
              >
                Upload PDFs to {channel.emoji} {channel.name}
              </button>
            </div>
            <div className="action-grid">
              <div className="action-block">
                <h4>Update chart</h4>
                <p>
                  <strong>Update chart</strong> maps new docked PDFs (Quick Dip).{' '}
                  <strong>Full rebuild</strong> regenerates the entire wiki from entries.
                </p>
                {isIngestPreview && (
                  <p className="text-[var(--accent)]">Preview dock — placeholder shells only.</p>
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
                </div>
                {(surfaceMutation.isError || rebuildMutation.isError) && (
                  <p className="mt-2 text-xs text-red-400">
                    {(surfaceMutation.error ?? rebuildMutation.error)?.message}
                  </p>
                )}
              </div>

              <div className="action-block">
                <h4>Deep Dive (LLM)</h4>
                <p>
                  Run automated Deep Dive on papers needing enrichment using{' '}
                  <strong>{appSettings?.llm.models.deep_dive ?? 'qwen3:32b'}</strong> (
                  {appSettings?.llm.deep_dive_provider ?? 'local'}). Output is marked{' '}
                  <em>needs review</em> until you verify.
                </p>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      deepDiveMutation.mutate({
                        slugs: enrichEntries.map((e) => e.slug),
                      })
                    }
                    disabled={
                      deepDiveMutation.isPending ||
                      isDiving ||
                      enrichEntries.length === 0 ||
                      !isPortfolio
                    }
                    className="btn-primary px-4 py-2 text-sm disabled:opacity-50"
                  >
                    {deepDiveMutation.isPending || isDiving
                      ? 'Running Deep Dive…'
                      : `Run Deep Dive (${enrichEntries.length})`}
                  </button>
                </div>
                {deepDiveMutation.isError && (
                  <p className="mt-2 text-xs text-red-400">{deepDiveMutation.error.message}</p>
                )}
                {enrichEntries.length === 0 && (
                  <p className="mt-2 text-xs text-[var(--muted)]">
                    No papers waiting for Deep Dive on this dock.
                  </p>
                )}
              </div>
            </div>
        </div>
      </div>
      )}

      {activeWorkspaceSection === 'section-query' && vault && (
        <div id="section-query" className="workspace-panel">
          <QueryPanel
            vaultId={vaultId}
            onJobStart={setActiveJobId}
            onQueryMeta={setQueryJobMeta}
          />
        </div>
      )}

          </div>
        </div>
      )}

      {activeJobId && (
        <section className="panel-card mb-6">
          <div className="flex items-center justify-between border-b border-[var(--border)] px-3 py-2">
            <span className="text-xs font-medium text-[var(--text)]">
              Job log
              {queryJobMeta && jobQuery.data?.type === 'query' && (
                <span className="ml-2 font-normal text-[var(--muted)]">
                  Query · {queryJobMeta.model}
                  {queryJobMeta.elapsed_s != null ? ` · ${queryJobMeta.elapsed_s}s` : ''}
                </span>
              )}
            </span>
            {jobStatus && (
              <span className={`text-xs font-medium uppercase ${statusColor(jobStatus)}`}>
                {jobStatus}
              </span>
            )}
          </div>
          {jobStatus === 'failed' && (
            <p className="border-b border-[var(--border)] px-3 py-2 text-xs text-red-400" role="alert">
              Job failed — check Ollama / GPU tunnel in Settings.
            </p>
          )}
          <pre className="max-h-48 overflow-auto p-3 font-mono text-[11px] leading-relaxed text-[var(--muted)]">
            {(logsQuery.data?.lines ?? []).join('\n') || 'Waiting…'}
          </pre>
        </section>
      )}

      {showBackToTop && (
        <button
          type="button"
          className="back-to-top"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          aria-label="Back to top"
        >
          ↑ Top
        </button>
      )}
      </div>

      <HowToPanel open={howToOpen} onClose={() => setHowToOpen(false)} />
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      {viewer && vault && (
        <ContentDrawer
          vaultId={vaultId}
          path={viewer.path}
          title={viewer.title}
          onClose={() => setViewer(null)}
        />
      )}

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
