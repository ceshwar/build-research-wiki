import type { Channel, ChannelStats, Job, JobLogs, UploadResult, Vault } from '../types'

const API = '/api'

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'object' && d && 'msg' in d ? String(d.msg) : String(d))).join('; ')
  }
  return fallback
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(formatApiError(err.detail, res.statusText || 'Request failed'))
  }
  return res.json()
}

export function fetchVaults() {
  return request<Vault[]>('/vaults')
}

export interface VaultValidateResult {
  ok: boolean
  path: string
  has_builder: boolean
  has_wiki: boolean
  paper_count: number
  suggested_name: string
  warnings: string[]
  error?: string
}

export function validateVaultPath(path: string) {
  return request<VaultValidateResult>('/vaults/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  })
}

export function pickVaultFolder() {
  return request<{ path: string | null; cancelled: boolean }>('/vaults/pick-folder', {
    method: 'POST',
  })
}

export function addVault(path: string, name?: string) {
  return request<Vault>('/vaults', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, name: name || null }),
  })
}

export function removeVault(vaultId: string) {
  return request<{ ok: boolean }>(`/vaults/${vaultId}`, { method: 'DELETE' })
}

export function fetchChannels(vaultId?: string, includeHidden = false) {
  const params = new URLSearchParams()
  if (vaultId) params.set('vault_id', vaultId)
  if (includeHidden) params.set('include_hidden', 'true')
  const q = params.toString()
  return request<Channel[]>(`/channels${q ? `?${q}` : ''}`)
}

export function createDock(vaultId: string, payload: import('../types').DockCreatePayload) {
  return request<Channel>(`/vaults/${vaultId}/docks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: payload.name,
      emoji: payload.emoji ?? '📁',
      description: payload.description ?? '',
      profile: payload.profile ?? 'ingest',
    }),
  })
}

export function dockArtifacts(vaultId: string, files: File[], channelId: string) {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  return request<UploadResult>(
    `/dock?vault_id=${vaultId}&channel_id=${channelId}`,
    { method: 'POST', body: form },
  )
}

export function surfaceInterval(
  vaultId: string,
  channelId: string,
  mode: 'auto' | 'incremental' | 'full' = 'auto',
) {
  return request<{ job_id: string; mode: string; channel_id: string }>(
    `/surface_interval?vault_id=${vaultId}&channel_id=${channelId}&mode=${mode}`,
    { method: 'POST' },
  )
}

export function startBuild(vaultId: string, mode: 'auto' | 'incremental' | 'full' = 'auto') {
  return request<{ job_id: string; mode: string }>(
    `/build/wiki?vault_id=${vaultId}&mode=${mode}`,
    { method: 'POST' },
  )
}

export function fetchIngestPrompt(vaultId: string, channelId: string) {
  return request<{ prompt: string; count: number; channel_id: string }>(
    `/ingest-prompt?vault_id=${vaultId}&channel_id=${channelId}`,
  )
}

export function fetchChartMap(vaultId: string, channelId: string) {
  return request<import('../types').ChartMap>(
    `/chart-map?vault_id=${vaultId}&channel_id=${channelId}`,
  )
}

export function fetchChartGraph(vaultId: string, channelId: string) {
  return request<import('../types').ChartGraph>(
    `/chart-graph?vault_id=${vaultId}&channel_id=${channelId}`,
  )
}

export function updateChartVerification(
  vaultId: string,
  channelId: string,
  slug: string,
  humanVerified: boolean,
  verifiedBy = 'human',
) {
  const params = new URLSearchParams({ vault_id: vaultId, channel_id: channelId, slug })
  return request<{
    slug: string
    channel_id: string
    human_verified: boolean
    verified_at: string
    verified_by: string
    job_id: string | null
  }>(`/chart-entry/verification?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ human_verified: humanVerified, verified_by: verifiedBy }),
  })
}

export function fetchLlmConfig() {
  return request<{
    ollama_url: string
    default_model: string
    embedding_model: string
    think: boolean
    stages: Record<string, string>
  }>('/llm-config')
}

export function removeFromChart(vaultId: string, channelId: string, slug: string) {
  const params = new URLSearchParams({ vault_id: vaultId, channel_id: channelId, slug })
  return request<{ slug: string; channel_id: string; deleted_files: string[]; job_id: string | null }>(
    `/chart-entry?${params}`,
    { method: 'DELETE' },
  )
}

export async function removeFromChartBatch(vaultId: string, channelId: string, slugs: string[]) {
  const params = new URLSearchParams({ vault_id: vaultId, channel_id: channelId })
  try {
    return await request<{ channel_id: string; removed: string[]; job_id: string | null }>(
      `/chart-remove?${params}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slugs }),
      },
    )
  } catch (e) {
    const msg = e instanceof Error ? e.message : ''
    if (!/not found/i.test(msg)) throw e
    // Older backends only expose DELETE /chart-entry — fall back per slug.
    const removed: string[] = []
    let job_id: string | null = null
    for (const slug of slugs) {
      const r = await removeFromChart(vaultId, channelId, slug)
      removed.push(r.slug)
      if (r.job_id) job_id = r.job_id
    }
    return { channel_id: channelId, removed, job_id }
  }
}

export function fetchJob(jobId: string) {
  return request<Job>(`/jobs/${jobId}`)
}

export function fetchJobLogs(jobId: string) {
  return request<JobLogs>(`/jobs/${jobId}/logs`)
}

export function fetchSettings() {
  return request<import('../types').AppSettings>('/settings')
}

export function updateSettings(patch: Partial<import('../types').AppSettings>) {
  return request<import('../types').AppSettings>('/settings', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
}

export function fetchVaultFile(vaultId: string, path: string) {
  const params = new URLSearchParams({ vault_id: vaultId, path })
  return request<{ path: string; content_type: string; content: string | null; size: number }>(
    `/vault-file?${params}`,
  )
}

export function runDeepDive(
  vaultId: string,
  channelId: string,
  opts: { slug?: string; slugs?: string[]; provider?: string; model?: string } = {},
) {
  const params = new URLSearchParams({ vault_id: vaultId, channel_id: channelId })
  return request<{ job_id: string; model: string; provider: string; slugs: string[] }>(
    `/deep-dive?${params}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        slug: opts.slug,
        slugs: opts.slugs ?? [],
        provider: opts.provider,
        model: opts.model,
      }),
    },
  )
}

export function runWikiQuery(
  vaultId: string,
  question: string,
  provider?: string,
  model?: string,
  scope: 'all' | 'verified' | 'needs_review' | 'uncharted' = 'all',
) {
  const params = new URLSearchParams({ vault_id: vaultId })
  return request<{ job_id: string; model: string; provider: string; question: string }>(
    `/query?${params}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, provider, model, scope }),
    },
  )
}

export function fetchQueryResult(jobId: string, question = '') {
  const params = new URLSearchParams({ question })
  return request<{
    job_id: string
    status: string
    question: string
    answer: string
    model: string
    elapsed_s?: number
    provider_kind?: string
  }>(`/query/${jobId}?${params}`)
}

export type { ChannelStats }
