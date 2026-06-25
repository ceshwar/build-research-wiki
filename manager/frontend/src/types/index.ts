export interface Channel {
  id: string
  name: string
  emoji: string
  description: string
  profile: 'portfolio' | 'ingest'
  raw_path: string
  extensions: string[]
  /** full = portfolio Quick Dip; preview = ingest shell only (Phase 3 full ingest) */
  chart_support: 'full' | 'preview'
  builtin?: boolean
  hidden?: boolean
}

export interface NeedsAttention {
  slug: string
  title: string
  status: 'scaffolded' | 'charted' | 'processed' | 'quick_dip' | 'needs_deep_dive'
}

export interface NeedsVerification {
  slug: string
  title: string
  status: string
  llm_model?: string
}

export interface ChannelStats {
  id: string
  name: string
  emoji?: string
  description: string
  profile: string
  raw_path: string
  extensions?: string[]
  artifact_count: number
  pending: number
  on_chart: number
  scaffolded: number
  charted: number
  processed: number
  needs_deep_dive: number
  quick_dip?: number
  needs_review: number
  needs_human_verification?: number
  human_verified_count?: number
  needs_attention: NeedsAttention[]
  needs_verification?: NeedsVerification[]
}

export interface Vault {
  id: string
  name: string
  path: string
  obsidian_vault_id?: string | null
  obsidian_links_ok?: boolean
  obsidian_link_path?: string | null
  artifact_count: number
  pdf_count: number
  paper_count: number
  theme_count: number
  last_build: string | null
  pending_artifacts: number
  on_chart: number
  scaffolded_count: number
  charted_count: number
  processed_count: number
  quick_dip_count?: number
  needs_deep_dive_count?: number
  needs_review_count: number
  needs_human_verification_count?: number
  human_verified_count?: number
  channels: ChannelStats[]
  user_added?: boolean
}

export interface Job {
  id: string
  type: string
  vault_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  started_at: string | null
  ended_at: string | null
  exit_code: number | null
  log_file: string | null
}

export interface JobLogs {
  job_id: string
  lines: string[]
  status: string
}

export interface UploadResult {
  files_added: number
  filenames: string[]
  channel_id: string
  channel_name: string
  raw_path: string
}

export interface DockCreatePayload {
  name: string
  emoji?: string
  description?: string
  profile?: 'portfolio' | 'ingest'
}

export interface ChartEntry {
  slug: string
  title: string
  status: string
  year: number | null
  venue: string
  pdf: string
  pdf_path: string
  themes: string[]
  overview: string
  entry: string
  wiki_page: string
  human_verified: boolean
  needs_human_verification: boolean
  llm_enriched: boolean
  llm_model: string
  enrichment_source: string
  territory: 'charted' | 'uncharted'
  verified_at: string
  verified_by: string
}

export interface ChartTheme {
  slug: string
  title: string
}

export interface ChartMap {
  channel_id: string
  channel_name: string
  profile: string
  raw_path: string
  wiki_folder: string
  themes: ChartTheme[]
  entries: ChartEntry[]
  raw_files: string[]
  awaiting_chart: string[]
}

export interface ChartGraphNode {
  id: string
  slug: string
  label: string
  type: string
  wiki_page: string
  status?: string | null
  human_verified?: boolean | null
  needs_human_verification?: boolean | null
  territory?: string | null
}

export interface ChartGraphEdge {
  source: string
  target: string
  kind: string
}

export interface ChartGraph {
  channel_id: string
  nodes: ChartGraphNode[]
  edges: ChartGraphEdge[]
  stats: Record<string, number>
  message?: string
}

export interface LlmModelsConfig {
  deep_dive: string
  charting: string
  query: string
}

export interface FrontierConfig {
  provider: string
  deep_dive_model: string
  query_model: string
}

export interface LlmSettings {
  deep_dive_provider: string
  query_provider: string
  ollama_url: string
  think: boolean
  model_catalog: string[]
  models: LlmModelsConfig
  frontier: FrontierConfig
}

export interface AppSettings {
  view_in: 'app' | 'obsidian'
  llm: LlmSettings
}
