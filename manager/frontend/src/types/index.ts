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
  needs_attention: NeedsAttention[]
}

export interface Vault {
  id: string
  name: string
  path: string
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
