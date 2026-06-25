import type { ChartEntry } from '../types'

export const ENRICHMENT_LABELS: Record<string, string> = {
  'quick-dip': 'Quick dip',
  'local-32b': 'Deep dive (32B)',
  'local-custom': 'Deep dive (local)',
  frontier: 'Deep dive (frontier)',
  human: 'Human charted',
}

export function enrichmentLabel(entry: Pick<ChartEntry, 'enrichment_source' | 'llm_model' | 'status'>) {
  const src = entry.enrichment_source
  if (src && ENRICHMENT_LABELS[src]) {
    if (src === 'local-custom' && entry.llm_model) return `Deep dive (${entry.llm_model})`
    return ENRICHMENT_LABELS[src]
  }
  if (entry.status === 'quick_dip') return 'Quick dip'
  if (entry.status === 'processed') return 'Deep dive'
  return ''
}

export function territoryLabel(territory: string) {
  return territory === 'uncharted' ? 'Uncharted' : 'Charted'
}
