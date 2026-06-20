import type { Channel, ChannelStats, Job, JobLogs, UploadResult, Vault } from '../types'

const API = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
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

export function removeFromChart(vaultId: string, channelId: string, slug: string) {
  const params = new URLSearchParams({ vault_id: vaultId, channel_id: channelId, slug })
  return request<{ slug: string; channel_id: string; deleted_files: string[]; job_id: string | null }>(
    `/chart-entry?${params}`,
    { method: 'DELETE' },
  )
}

export function fetchJob(jobId: string) {
  return request<Job>(`/jobs/${jobId}`)
}

export function fetchJobLogs(jobId: string) {
  return request<JobLogs>(`/jobs/${jobId}/logs`)
}

export type { ChannelStats }
