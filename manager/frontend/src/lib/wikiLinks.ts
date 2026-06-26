/** Resolve wiki slugs to vault-relative paths and expand [[wikilinks]] for MarkdownViewer. */

export type WikiSlugHints = {
  papers?: string[]
  themes?: string[]
  concepts?: string[]
  entities?: string[]
  sources?: string[]
}

export function wikiPathForSlug(slug: string, hints?: WikiSlugHints): string {
  const s = slug.trim().toLowerCase()
  if (hints?.themes?.includes(s)) return `wiki/themes/${s}.md`
  if (hints?.papers?.includes(s)) return `wiki/papers/${s}.md`
  if (hints?.concepts?.includes(s)) return `wiki/concepts/${s}.md`
  if (hints?.entities?.includes(s)) return `wiki/entities/${s}.md`
  if (hints?.sources?.includes(s)) return `wiki/sources/${s}.md`
  return `wiki/papers/${s}.md`
}

export function expandWikilinks(text: string): string {
  return text.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_m, raw, label) => {
    const target = String(raw).trim()
    const display = (label || target).trim()
    const slug = target.split('/').pop()?.replace(/\.md$/i, '') || target
    return `[${display}](portolan://${encodeURIComponent(slug)})`
  })
}

export function isChatModel(modelId: string): boolean {
  const low = modelId.toLowerCase()
  return !low.includes('embed') && !low.includes('nomic-embed')
}
