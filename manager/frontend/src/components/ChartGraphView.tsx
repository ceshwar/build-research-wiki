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
  | 'needs_verification'
  | 'uncharted'

type GraphLayerId = 'paper' | 'theme' | 'concept' | 'entity' | 'synthesis' | 'source'

const LAYERS_STORAGE_KEY = 'portolan-graph-layers'
const LEGACY_LAYERS_STORAGE_KEY = 'ideaverse-graph-layers'
const DEFAULT_GRAPH_LAYERS: GraphLayerId[] = ['paper', 'theme', 'concept']

/** Base node colors — navy/orange app palette; accent orange reserved for hover highlight only. */
const LAYER_COLORS: Record<GraphLayerId, string> = {
  paper: '#6b8cae',
  theme: '#6366f1',
  concept: '#2dd4bf',
  entity: '#4ade80',
  synthesis: '#e879f9',
  source: '#94a3b8',
}

const PAPER_STATUS_COLORS: Record<string, string> = {
  processed: '#059669',
  quick_dip: '#0ea5e9',
  needs_deep_dive: '#a16207',
  scaffolded: '#8b7ec8',
  charted: '#64748b',
}

export const GRAPH_LAYER_OPTIONS: {
  id: GraphLayerId
  label: string
  color: string
  defaultOn: boolean
}[] = [
  { id: 'paper', label: 'Papers', color: LAYER_COLORS.paper, defaultOn: true },
  { id: 'theme', label: 'Themes', color: LAYER_COLORS.theme, defaultOn: true },
  { id: 'concept', label: 'Concepts', color: LAYER_COLORS.concept, defaultOn: true },
  { id: 'entity', label: 'Entities', color: LAYER_COLORS.entity, defaultOn: false },
  { id: 'synthesis', label: 'Syntheses', color: LAYER_COLORS.synthesis, defaultOn: false },
  { id: 'source', label: 'Sources', color: LAYER_COLORS.source, defaultOn: false },
]

const GRAPH_HEIGHT = 520
const PROXIMITY_RADIUS = 72

function loadEnabledLayers(): Set<GraphLayerId> {
  try {
    let raw = localStorage.getItem(LAYERS_STORAGE_KEY)
    if (!raw) {
      raw = localStorage.getItem(LEGACY_LAYERS_STORAGE_KEY)
      if (raw) {
        localStorage.setItem(LAYERS_STORAGE_KEY, raw)
        localStorage.removeItem(LEGACY_LAYERS_STORAGE_KEY)
      }
    }
    if (raw) {
      const parsed = JSON.parse(raw) as GraphLayerId[]
      if (Array.isArray(parsed) && parsed.length > 0) {
        return new Set(parsed)
      }
    }
  } catch {
    /* ignore */
  }
  return new Set(DEFAULT_GRAPH_LAYERS)
}

function layerIdForNodeType(type: string): GraphLayerId | null {
  if (type === 'paper') return 'paper'
  if (type === 'theme') return 'theme'
  if (type === 'concept') return 'concept'
  if (type === 'entity') return 'entity'
  if (type === 'synthesis') return 'synthesis'
  if (type === 'source') return 'source'
  return null
}

export function filterGraphLayers(graph: ChartGraph, enabled: Set<GraphLayerId>): ChartGraph {
  const nodes = graph.nodes.filter((n) => {
    const layer = layerIdForNodeType(n.type)
    return layer != null && enabled.has(layer)
  })
  const ids = new Set(nodes.map((n) => n.id))
  const edges = graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target))
  const stats: Record<string, number> = {}
  for (const n of nodes) {
    stats[n.type] = (stats[n.type] ?? 0) + 1
  }
  return { ...graph, nodes, edges, stats }
}

function readAccentColor(): string {
  const v = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()
  return v || '#ea580c'
}

function accentAlpha(hex: string, alpha: number): string {
  const h = hex.replace('#', '')
  if (h.length !== 6) return `rgba(234, 88, 12, ${alpha})`
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function paperColor(status: string | null | undefined): string {
  if (!status) return LAYER_COLORS.paper
  return PAPER_STATUS_COLORS[status] ?? LAYER_COLORS.paper
}

function nodeColor(node: ChartGraphNode): string {
  if (node.type === 'paper') {
    if (node.needs_human_verification) return '#d97706'
    return paperColor(node.status)
  }
  const layer = layerIdForNodeType(node.type)
  return layer ? LAYER_COLORS[layer] : '#94a3b8'
}

function nodeRadius(node: ChartGraphNode): number {
  switch (node.type) {
    case 'paper':
      return 8
    case 'theme':
      return 7
    case 'synthesis':
      return 6
    default:
      return 5
  }
}

function truncateLabel(label: string, max = 22): string {
  if (label.length <= max) return label
  return `${label.slice(0, max - 1)}…`
}

function linkKey(source: string, target: string): string {
  return `${source}|${target}`
}

function linkEndpointIds(link: { source: unknown; target: unknown }): { source: string; target: string } {
  const source =
    typeof link.source === 'object' && link.source !== null && 'id' in link.source
      ? String((link.source as { id: string }).id)
      : String(link.source)
  const target =
    typeof link.target === 'object' && link.target !== null && 'id' in link.target
      ? String((link.target as { id: string }).id)
      : String(link.target)
  return { source, target }
}

function paperMatchesFilter(node: ChartGraphNode, filter: StatFilter): boolean {
  const status = node.status
  if (filter === 'all' || filter === 'on_chart') return true
  if (filter === 'needs_verification') return !!node.needs_human_verification
  if (filter === 'uncharted') return node.territory === 'uncharted'
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
      .filter((n) => n.type === 'paper' && paperMatchesFilter(n, filter))
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

type GraphNode = ChartGraphNode & { x?: number; y?: number; vx?: number; vy?: number; fx?: number; fy?: number }
type GraphLink = { source: string | GraphNode; target: string | GraphNode; kind: string }

type GraphData = {
  nodes: GraphNode[]
  links: GraphLink[]
}

type PointerState = { x: number; y: number; active: boolean }

export function ChartGraphView({
  graph,
  vaultPath,
  obsidianVaultId,
  statFilter,
  loading,
  active = true,
  onOpenPage,
}: {
  graph?: ChartGraph
  vaultPath: string
  obsidianVaultId?: string | null
  statFilter: StatFilter
  loading?: boolean
  active?: boolean
  onOpenPage?: (path: string, title?: string) => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<ForceGraphMethods<GraphNode, GraphLink> | undefined>(undefined)
  const fitPendingRef = useRef(true)
  const hoveredIdRef = useRef<string | null>(null)
  const highlightIdsRef = useRef<Set<string>>(new Set())
  const highlightLinkKeysRef = useRef<Set<string>>(new Set())
  const pointerRef = useRef<PointerState>({ x: 0, y: 0, active: false })
  const accentRef = useRef(readAccentColor())
  const [size, setSize] = useState({ width: 640, height: GRAPH_HEIGHT })
  const [enabledLayers, setEnabledLayers] = useState<Set<GraphLayerId>>(loadEnabledLayers)
  const [, bumpRender] = useState(0)

  const filteredByStatus = useMemo(
    () => (graph ? filterGraphData(graph, statFilter) : undefined),
    [graph, statFilter],
  )

  const filtered = useMemo(
    () => (filteredByStatus ? filterGraphLayers(filteredByStatus, enabledLayers) : undefined),
    [filteredByStatus, enabledLayers],
  )

  const toggleLayer = useCallback((id: GraphLayerId) => {
    setEnabledLayers((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        if (next.size <= 1) return prev
        next.delete(id)
      } else {
        next.add(id)
      }
      localStorage.setItem(LAYERS_STORAGE_KEY, JSON.stringify([...next]))
      fitPendingRef.current = true
      hoveredIdRef.current = null
      highlightIdsRef.current = new Set()
      highlightLinkKeysRef.current = new Set()
      return next
    })
  }, [])

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

  const adjacency = useMemo(() => {
    const neighbors = new Map<string, Set<string>>()
    for (const edge of graphData.links) {
      const { source, target } = linkEndpointIds(edge)
      if (!neighbors.has(source)) neighbors.set(source, new Set())
      if (!neighbors.has(target)) neighbors.set(target, new Set())
      neighbors.get(source)!.add(target)
      neighbors.get(target)!.add(source)
    }
    return neighbors
  }, [graphData.links])

  const setHighlight = useCallback(
    (nodeId: string | null) => {
      hoveredIdRef.current = nodeId
      if (!nodeId) {
        highlightIdsRef.current = new Set()
        highlightLinkKeysRef.current = new Set()
        return
      }
      const nearby = adjacency.get(nodeId) ?? new Set<string>()
      highlightIdsRef.current = new Set([nodeId, ...nearby])
      const keys = new Set<string>()
      for (const link of graphData.links) {
        const { source, target } = linkEndpointIds(link)
        if (source === nodeId || target === nodeId) {
          keys.add(linkKey(source, target))
        }
      }
      highlightLinkKeysRef.current = keys
    },
    [adjacency, graphData.links],
  )

  const measureSize = useCallback(() => {
    const el = containerRef.current
    if (!el) return
    const width = el.clientWidth
    if (width > 0) {
      setSize({ width, height: GRAPH_HEIGHT })
    }
  }, [])

  useEffect(() => {
    accentRef.current = readAccentColor()
  }, [])

  useEffect(() => {
    if (!active) return
    measureSize()
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(() => measureSize())
    ro.observe(el)
    window.addEventListener('resize', measureSize)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', measureSize)
    }
  }, [active, measureSize])

  useEffect(() => {
    fitPendingRef.current = true
    setHighlight(null)
  }, [graphData.nodes.length, statFilter, enabledLayers, setHighlight])

  const fitGraph = useCallback(() => {
    const fg = graphRef.current
    if (!fg || graphData.nodes.length === 0) return
    fg.zoomToFit(400, 56)
  }, [graphData.nodes.length])

  // Land the graph framed quickly: nodes have positions after warmup, so fit a few times
  // early instead of waiting for the full simulation cooldown (onEngineStop fits as a backstop).
  useEffect(() => {
    if (!active || graphData.nodes.length === 0) return
    const timers = [250, 700, 1400].map((ms) => window.setTimeout(() => fitGraph(), ms))
    return () => timers.forEach((t) => window.clearTimeout(t))
  }, [active, graphData.nodes.length, statFilter, enabledLayers, fitGraph])

  const handleEngineStop = useCallback(() => {
    if (!fitPendingRef.current) return
    fitPendingRef.current = false
    fitGraph()
  }, [fitGraph])

  const zoomBy = useCallback((factor: number) => {
    const fg = graphRef.current
    if (!fg) return
    const scale = fg.zoom()
    fg.zoom(scale * factor, 300)
  }, [])

  const proximityForNode = useCallback((node: GraphNode, focusId: string | null) => {
    const ptr = pointerRef.current
    if (!ptr.active || focusId) return 0
    const nx = node.x ?? 0
    const ny = node.y ?? 0
    const dx = nx - ptr.x
    const dy = ny - ptr.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist >= PROXIMITY_RADIUS) return 0
    return 1 - dist / PROXIMITY_RADIUS
  }, [])

  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const x = node.x ?? 0
    const y = node.y ?? 0
    const baseR = nodeRadius(node)
    const accent = accentRef.current
    const focusId = hoveredIdRef.current
    const highlighted = focusId ? highlightIdsRef.current.has(node.id) : false
    const isFocus = focusId === node.id
    const dimmed = !!focusId && !highlighted
    const prox = proximityForNode(node, focusId)
    const t = performance.now() / 1000
    const wobble = prox * 0.55
    const phase = node.id.charCodeAt(0) * 0.65 + t * 7
    const shakeX = (Math.sin(phase) * wobble) / globalScale
    const shakeY = (Math.cos(phase * 1.25) * wobble) / globalScale
    const drawX = x + shakeX
    const drawY = y + shakeY
    const r = baseR * (1 + prox * 0.16)

    if (dimmed) ctx.globalAlpha = 0.2

    const fill = highlighted ? accent : nodeColor(node)

    if (isFocus) {
      ctx.beginPath()
      ctx.arc(drawX, drawY, r + 5 / globalScale, 0, 2 * Math.PI, false)
      ctx.fillStyle = accentAlpha(accent, 0.28)
      ctx.fill()
    } else if (prox > 0.08) {
      ctx.beginPath()
      ctx.arc(drawX, drawY, r + 3 / globalScale, 0, 2 * Math.PI, false)
      ctx.fillStyle = accentAlpha(accent, 0.12 * prox)
      ctx.fill()
    }

    ctx.beginPath()
    ctx.arc(drawX, drawY, r, 0, 2 * Math.PI, false)
    ctx.fillStyle = fill
    ctx.fill()
    ctx.strokeStyle = highlighted ? accentAlpha(accent, 0.95) : 'rgba(255, 255, 255, 0.35)'
    ctx.lineWidth = (highlighted ? 2.4 : 1.2) / globalScale
    ctx.stroke()

    const fontSize = Math.max(10 / globalScale, 2.5)
    const text = truncateLabel(node.label)
    ctx.font = `600 ${fontSize}px system-ui, -apple-system, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    const textY = drawY + r + 3 / globalScale
    const metrics = ctx.measureText(text)
    const padX = 4 / globalScale
    const padY = 2 / globalScale
    const boxW = metrics.width + padX * 2
    const boxH = fontSize + padY * 2
    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)'
    ctx.fillRect(drawX - boxW / 2, textY - padY, boxW, boxH)
    ctx.fillStyle = '#e8edf5'
    ctx.fillText(text, drawX, textY)

    ctx.globalAlpha = 1
  }, [proximityForNode])

  const defaultLinkColor = useCallback((kind: string) => {
    return kind === 'theme' ? 'rgba(99, 102, 241, 0.4)' : 'rgba(107, 140, 174, 0.45)'
  }, [])

  const linkColor = useCallback(
    (link: GraphLink) => {
      const focusId = hoveredIdRef.current
      if (!focusId) return defaultLinkColor(link.kind)
      const { source, target } = linkEndpointIds(link)
      const key = linkKey(source, target)
      if (highlightLinkKeysRef.current.has(key)) {
        return accentAlpha(accentRef.current, 0.88)
      }
      return 'rgba(148, 163, 184, 0.1)'
    },
    [defaultLinkColor],
  )

  const linkWidth = useCallback((link: GraphLink) => {
    const focusId = hoveredIdRef.current
    if (!focusId) return link.kind === 'theme' ? 1.5 : 1
    const { source, target } = linkEndpointIds(link)
    return highlightLinkKeysRef.current.has(linkKey(source, target)) ? 2.8 : 0.5
  }, [])

  const onNodeClick = useCallback(
    (node: GraphNode) => {
      if (!node.wiki_page) return
      if (onOpenPage) {
        onOpenPage(node.wiki_page, node.label)
        return
      }
      window.location.href = obsidianHref(node.wiki_page, vaultPath, obsidianVaultId)
    },
    [vaultPath, obsidianVaultId, onOpenPage],
  )

  useEffect(() => {
    const fg = graphRef.current
    if (!fg || !active) return

    const linkForce = fg.d3Force('link')
    if (linkForce && 'distance' in linkForce) {
      linkForce.distance(96)
    }
    const chargeForce = fg.d3Force('charge')
    if (chargeForce && 'strength' in chargeForce) {
      chargeForce.strength(-240)
    }
    const collideForce = fg.d3Force('collide')
    if (collideForce && 'radius' in collideForce) {
      collideForce.radius((n: GraphNode) => nodeRadius(n) + 14)
    }
    fg.d3Force('pointer', null)
  }, [active, graphData.nodes.length])

  useEffect(() => {
    const wrap = containerRef.current
    if (!wrap || !active) return

    let anim = 0
    const startAnim = () => {
      if (anim) return
      const loop = () => {
        if (!pointerRef.current.active) {
          anim = 0
          return
        }
        bumpRender((v) => v + 1)
        anim = requestAnimationFrame(loop)
      }
      anim = requestAnimationFrame(loop)
    }

    const updatePointer = (clientX: number, clientY: number) => {
      const fg = graphRef.current
      const canvas = wrap.querySelector('canvas')
      if (!fg || !canvas) return
      const rect = canvas.getBoundingClientRect()
      const coords = fg.screen2GraphCoords(clientX - rect.left, clientY - rect.top)
      pointerRef.current = { x: coords.x, y: coords.y, active: true }
      startAnim()
    }

    const onMove = (e: MouseEvent) => updatePointer(e.clientX, e.clientY)
    const onLeave = () => {
      pointerRef.current.active = false
      if (anim) {
        cancelAnimationFrame(anim)
        anim = 0
      }
    }

    const attach = () => {
      const canvas = wrap.querySelector('canvas')
      if (!canvas) return false
      canvas.addEventListener('mousemove', onMove)
      canvas.addEventListener('mouseleave', onLeave)
      return true
    }

    if (!attach()) {
      const t = window.setTimeout(attach, 120)
      return () => window.clearTimeout(t)
    }

    return () => {
      onLeave()
      const canvas = wrap.querySelector('canvas')
      canvas?.removeEventListener('mousemove', onMove)
      canvas?.removeEventListener('mouseleave', onLeave)
    }
  }, [active, graphData.nodes.length])

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
    if (filteredByStatus && filteredByStatus.nodes.length > 0) {
      return (
        <div className="empty-map">
          No nodes for the selected layers. Turn on more types in <strong>Show</strong>.
        </div>
      )
    }
    return <div className="empty-map">No papers match this filter.</div>
  }

  const stats = filtered?.stats ?? {}

  return (
    <div className="chart-graph">
      <div className="chart-graph__layers" role="group" aria-label="Show node types">
        <span className="chart-graph__layers-label">Show</span>
        {GRAPH_LAYER_OPTIONS.map((layer) => {
          const on = enabledLayers.has(layer.id)
          return (
            <button
              key={layer.id}
              type="button"
              className={`graph-layer-chip${on ? ' graph-layer-chip--on' : ''}`}
              aria-pressed={on}
              onClick={() => toggleLayer(layer.id)}
            >
              <span
                className="graph-layer-chip__dot"
                style={{ background: layer.color }}
                aria-hidden="true"
              />
              {layer.label}
            </button>
          )
        })}
      </div>
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
        <span className="chart-graph__nav-hint">
          Scroll to zoom · drag canvas to pan · click node to open in Obsidian
        </span>
      </div>
      <div ref={containerRef} className="chart-graph__canvas-wrap">
        <div className="chart-graph__zoom" role="toolbar" aria-label="Graph zoom">
          <button type="button" className="chart-graph__zoom-btn" onClick={() => zoomBy(1.35)} title="Zoom in">
            +
          </button>
          <button type="button" className="chart-graph__zoom-btn" onClick={() => zoomBy(1 / 1.35)} title="Zoom out">
            −
          </button>
          <button type="button" className="chart-graph__zoom-btn chart-graph__zoom-btn--wide" onClick={fitGraph} title="Fit graph">
            Fit
          </button>
        </div>
        <ForceGraph2D
          ref={graphRef}
          width={size.width}
          height={size.height}
          graphData={graphData}
          backgroundColor="rgba(12, 18, 32, 0.55)"
          nodeId="id"
          nodeVal={(n) => nodeRadius(n) ** 2}
          nodeCanvasObject={paintNode}
          nodeCanvasObjectMode={() => 'replace'}
          nodePointerAreaPaint={(node, color, ctx) => {
            const r = nodeRadius(node) + 6
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(node.x ?? 0, node.y ?? 0, r, 0, 2 * Math.PI, false)
            ctx.fill()
          }}
          linkColor={linkColor}
          linkWidth={linkWidth}
          linkDirectionalArrowLength={2.5}
          linkDirectionalArrowRelPos={1}
          linkDirectionalArrowColor={(link) => linkColor(link)}
          onNodeClick={onNodeClick}
          onNodeHover={(n) => {
            setHighlight(n?.id ?? null)
            bumpRender((v) => v + 1)
          }}
          onBackgroundClick={() => {
            setHighlight(null)
            bumpRender((v) => v + 1)
          }}
          onEngineStop={handleEngineStop}
          enableNodeDrag
          enablePanInteraction
          enableZoomInteraction
          minZoom={0.08}
          maxZoom={12}
          warmupTicks={80}
          cooldownTicks={180}
          d3AlphaDecay={0.018}
          d3VelocityDecay={0.32}
        />
      </div>
    </div>
  )
}
