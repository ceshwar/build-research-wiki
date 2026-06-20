import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d'
import type { ChartGraph, ChartGraphNode } from '../types'

type StatFilter =
  | 'all'
  | 'on_chart'
  | 'pending'
  | 'quick_dip'
  | 'enrich'
  | 'processed'
  | 'needs_deep_dive'
  | 'charted'

const NODE_COLORS: Record<string, string> = {
  paper_processed: '#22c55e',
  paper_quick_dip: '#38bdf8',
  paper_needs_deep_dive: '#f59e0b',
  paper_scaffolded: '#a78bfa',
  paper_charted: '#94a3b8',
  paper: '#64748b',
  theme: '#8b5cf6',
  concept: '#3b82f6',
  entity: '#10b981',
  synthesis: '#f97316',
  source: '#6b7280',
  page: '#9ca3af',
}

function paperColor(status: string | null | undefined): string {
  if (!status) return NODE_COLORS.paper
  return NODE_COLORS[`paper_${status}`] ?? NODE_COLORS.paper
}

function nodeColor(node: ChartGraphNode): string {
  if (node.type === 'paper') return paperColor(node.status)
  return NODE_COLORS[node.type] ?? NODE_COLORS.page
}

function nodeRadius(node: ChartGraphNode): number {
  switch (node.type) {
    case 'paper':
      return 7
    case 'theme':
      return 6
    case 'synthesis':
      return 5.5
    default:
      return 4.5
  }
}

function paperMatchesFilter(status: string | null | undefined, filter: StatFilter): boolean {
  if (filter === 'all' || filter === 'on_chart') return true
  if (filter === 'quick_dip') return status === 'quick_dip'
  if (filter === 'processed') return status === 'processed'
  if (filter === 'needs_deep_dive') return status === 'needs_deep_dive'
  if (filter === 'charted') return status === 'charted'
  if (filter === 'enrich') return status === 'quick_dip' || status === 'needs_deep_dive'
  return true
}

export function filterGraphData(graph: ChartGraph, filter: StatFilter): ChartGraph {
  if (filter === 'all' || filter === 'on_chart' || filter === 'pending') return graph

  const visiblePapers = new Set(
    graph.nodes
      .filter((n) => n.type === 'paper' && paperMatchesFilter(n.status, filter))
      .map((n) => n.id),
  )
  const connected = new Set(visiblePapers)
  for (const edge of graph.edges) {
    if (visiblePapers.has(edge.source)) connected.add(edge.target)
    if (visiblePapers.has(edge.target)) connected.add(edge.source)
  }

  const nodes = graph.nodes.filter(
    (n) => (n.type === 'paper' ? visiblePapers.has(n.id) : connected.has(n.id)),
  )
  const ids = new Set(nodes.map((n) => n.id))
  const edges = graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target))
  return { ...graph, nodes, edges }
}

function obsidianHref(
  reefPath: string,
  vaultPath: string,
  obsidianVaultId?: string | null,
): string {
  const rel = reefPath.replace(/^\//, '')
  if (obsidianVaultId) {
    return `obsidian://open?vault=${encodeURIComponent(obsidianVaultId)}&file=${encodeURIComponent(rel)}`
  }
  const base = vaultPath.replace(/\/$/, '')
  return `obsidian://open?path=${encodeURIComponent(`${base}/${rel}`)}`
}

type GraphData = {
  nodes: (ChartGraphNode & { x?: number; y?: number })[]
  links: { source: string; target: string; kind: string }[]
}

export function ChartGraphView({
  graph,
  vaultPath,
  obsidianVaultId,
  statFilter,
  loading,
}: {
  graph?: ChartGraph
  vaultPath: string
  obsidianVaultId?: string | null
  statFilter: StatFilter
  loading?: boolean
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<ForceGraphMethods<ChartGraphNode, { kind: string }> | undefined>(undefined)
  const [size, setSize] = useState({ width: 640, height: 480 })
  const [hovered, setHovered] = useState<ChartGraphNode | null>(null)

  const filtered = useMemo(
    () => (graph ? filterGraphData(graph, statFilter) : undefined),
    [graph, statFilter],
  )

  const graphData: GraphData = useMemo(() => {
    if (!filtered) return { nodes: [], links: [] }
    return {
      nodes: filtered.nodes.map((n) => ({ ...n })),
      links: filtered.edges.map((e) => ({
        source: e.source,
        target: e.target,
        kind: e.kind,
      })),
    }
  }, [filtered])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver((entries) => {
      const { width } = entries[0]?.contentRect ?? { width: 640 }
      setSize({ width: Math.max(320, width), height: 480 })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (graphData.nodes.length && graphRef.current) {
      graphRef.current.zoomToFit(400, 40)
    }
  }, [graphData.nodes.length, statFilter])

  const onNodeClick = useCallback(
    (node: ChartGraphNode) => {
      if (!node.wiki_page) return
      window.location.href = obsidianHref(node.wiki_page, vaultPath, obsidianVaultId)
    },
    [vaultPath, obsidianVaultId],
  )

  if (loading) {
    return <p className="text-sm text-[var(--muted)]">Loading graph…</p>
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="empty-map">
        <p>{graph?.message || 'No graph data for this dock.'}</p>
      </div>
    )
  }

  if (graphData.nodes.length === 0) {
    return <div className="empty-map">No papers match this filter.</div>
  }

  const stats = filtered?.stats ?? {}

  return (
    <div className="chart-graph">
      <div className="chart-graph__meta">
        <span>
          {graphData.nodes.length} nodes · {graphData.links.length} links
        </span>
        {Object.keys(stats).length > 0 && (
          <span className="chart-graph__stats">
            {Object.entries(stats)
              .map(([k, v]) => `${v} ${k}${v === 1 ? '' : 's'}`)
              .join(' · ')}
          </span>
        )}
      </div>
      <div ref={containerRef} className="chart-graph__canvas-wrap">
        <ForceGraph2D
          ref={graphRef}
          width={size.width}
          height={size.height}
          graphData={graphData}
          nodeId="id"
          nodeLabel={(n) => `${n.label} (${n.type.replace(/_/g, ' ')})`}
          nodeVal={(n) => nodeRadius(n)}
          nodeColor={(n) => nodeColor(n)}
          linkColor={(l) => (l.kind === 'theme' ? 'rgba(139,92,246,0.35)' : 'rgba(148,163,184,0.45)')}
          linkWidth={(l) => (l.kind === 'theme' ? 1.5 : 1)}
          onNodeClick={onNodeClick}
          onNodeHover={(n) => setHovered(n)}
          cooldownTicks={80}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
        />
      </div>
      <div className="chart-graph__legend" aria-label="Node types">
        {[
          ['paper', 'Paper'],
          ['theme', 'Theme'],
          ['concept', 'Concept'],
          ['entity', 'Entity'],
          ['synthesis', 'Synthesis'],
        ].map(([type, label]) => (
          <span key={type} className="chart-graph__legend-item">
            <span
              className="chart-graph__legend-swatch"
              style={{ background: NODE_COLORS[type] ?? NODE_COLORS.page }}
            />
            {label}
          </span>
        ))}
      </div>
      {hovered && (
        <p className="chart-graph__hint">
          Click <strong>{hovered.label}</strong> to open in Obsidian
        </p>
      )}
    </div>
  )
}
