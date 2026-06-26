import type { ChartEntry } from '../types'

function shortModel(model: string) {
  const part = model.split(':').pop() || model
  return part.length > 18 ? `${part.slice(0, 16)}…` : part
}

/** Trust tier for portfolio papers (user-facing workflow). */
export type TrustTier = 'deep_dive' | 'quick_dip' | 'uncharted'

export function trustTier(entry: ChartEntry): TrustTier {
  if (entry.human_verified) return 'deep_dive'
  if (entry.llm_enriched) return 'quick_dip'
  return 'uncharted'
}

/** One status pill per paper — Uncharted → Quick Dip (LLM) → Deep Dive (verified). */
export function entryStatusPill(entry: ChartEntry) {
  const tier = trustTier(entry)
  if (tier === 'deep_dive') {
    return {
      icon: '🦑',
      label: 'Deep dive',
      title: entry.llm_model
        ? `Verified · ${entry.llm_model}`
        : 'Deep dive — human-reviewed or hand-charted',
      className: 'status-pill status-pill--deep',
    }
  }
  if (tier === 'quick_dip') {
    return {
      icon: '🤿',
      label: entry.llm_model ? `Quick dip · ${shortModel(entry.llm_model)}` : 'Quick dip',
      title: 'LLM-ingested — needs human review before Deep Dive',
      className: 'status-pill status-pill--quick',
    }
  }
  const hint =
    entry.status === 'needs_deep_dive'
      ? 'Charted — run Quick Dip (LLM)'
      : entry.status === 'quick_dip'
        ? 'PDF surfaced — run Quick Dip (LLM)'
        : 'On chart — awaiting Quick Dip or hand enrichment'
  return {
    icon: '◎',
    label: 'Uncharted',
    title: hint,
    className: 'status-pill status-pill--uncharted',
  }
}

/** LLM-ingested, not yet verified (Quick Dip / needs review). */
export function isQuickDipReview(entry: ChartEntry) {
  return entry.llm_enriched && !entry.human_verified
}

/** Human-verified Deep Dive. */
export function isDeepDiveVerified(entry: ChartEntry) {
  return entry.human_verified
}

/** Not LLM-ingested and not yet Deep dive (verified). */
export function isUncharted(entry: ChartEntry) {
  return trustTier(entry) === 'uncharted'
}

/** @deprecated use isQuickDipReview */
export const isNeedsReview = isQuickDipReview

/** @deprecated use isDeepDiveVerified */
export const isVerifiedEntry = isDeepDiveVerified
