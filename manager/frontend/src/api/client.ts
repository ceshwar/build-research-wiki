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

export function fetchChannels() {
  return request<Channel[]>('/channels')
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

export function fetchJob(jobId: string) {
  return request<Job>(`/jobs/${jobId}`)
}

export function fetchJobLogs(jobId: string) {
  return request<JobLogs>(`/jobs/${jobId}/logs`)
}

export type { ChannelStats }
