/** Resolve wiki slugs to vault-relative paths and expand [[wikilinks]] for MarkdownViewer. */

export type WikiSlugHints = {
  papers?: string[]
  themes?: string[]
  concepts?: string[]
  entities?: string[]
  sources?: string[]
}

export type WikiPathResolver = {
  hints?: WikiSlugHints
  /** slug -> vault-relative wiki path (e.g. from chart map / graph) */
  pathsBySlug?: Record<string, string>
}

export type WikiPageRef = {
  slug: string
  wiki_page?: string
  type?: string
}

const SLUG_RE = /^[a-z0-9][-a-z0-9_]*$/i
const HINT_BUCKET: Record<string, keyof WikiSlugHints> = {
  paper: 'papers',
  theme: 'themes',
  concept: 'concepts',
  entity: 'entities',
  source: 'sources',
}

/** Normalize [[target]], optional path, .md suffix, and #anchors to a slug. */
export function slugFromWikiTarget(target: string): string {
  const raw = target.trim().split('|')[0].split('#')[0].trim()
  const last = raw.split('/').pop() || raw
  return last.replace(/\.md$/i, '').toLowerCase()
}

/** All slugs referenced by Obsidian [[wikilinks]] in markdown text. */
export function extractWikilinkSlugs(text: string): string[] {
  const slugs: string[] = []
  const seen = new Set<string>()
  for (const match of text.matchAll(/\[\[([^\]]+)\]\]/g)) {
    const slug = slugFromWikiTarget(match[1])
    if (slug && !seen.has(slug)) {
      seen.add(slug)
      slugs.push(slug)
    }
  }
  return slugs
}

export function buildWikiResolver(
  entries?: WikiPageRef[],
  graphNodes?: WikiPageRef[],
): WikiPathResolver {
  const pathsBySlug: Record<string, string> = {}
  const hints: WikiSlugHints = {
    papers: [],
    themes: [],
    concepts: [],
    entities: [],
    sources: [],
  }

  const add = (slug: string, wikiPage?: string, type?: string) => {
    const s = slug.trim().toLowerCase()
    if (!s) return
    if (wikiPage) pathsBySlug[s] = wikiPage
    const bucket = type ? HINT_BUCKET[type] : undefined
    if (bucket) {
      const list = hints[bucket]!
      if (!list.includes(s)) list.push(s)
    }
  }

  for (const e of entries ?? []) add(e.slug, e.wiki_page, e.type ?? 'paper')
  for (const n of graphNodes ?? []) add(n.slug, n.wiki_page, n.type)

  return { hints, pathsBySlug }
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

export function resolveWikiPath(slug: string, resolver?: WikiPathResolver): string {
  const s = slug.trim().toLowerCase()
  if (resolver?.pathsBySlug?.[s]) return resolver.pathsBySlug[s]
  return wikiPathForSlug(s, resolver?.hints)
}

/** Extract a chart slug from portolan://, wiki/…, or bare markdown hrefs. */
export function parseWikiLinkHref(href: string | undefined | null): string | null {
  if (!href) return null
  const trimmed = href.trim()
  if (!trimmed) return null

  if (trimmed.startsWith('portolan://')) {
    const slug = decodeURIComponent(trimmed.slice('portolan://'.length)).split('/').pop() || ''
    return slugFromWikiTarget(slug) || null
  }

  const wikiMatch = trimmed.match(
    /^(?:\/)?wiki\/(papers|themes|concepts|entities|sources)\/([^/?#]+?)(?:\.md)?(?:#.*)?$/i,
  )
  if (wikiMatch) return wikiMatch[2].toLowerCase()

  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed)) return null

  const bare = trimmed.replace(/^\/+/, '').replace(/\.md$/i, '')
  const last = bare.split('/').pop()?.split('#')[0] || ''
  if (SLUG_RE.test(last)) return last.toLowerCase()

  return null
}

export function expandWikilinks(text: string): string {
  let out = text.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_m, raw, label) => {
    const target = String(raw).trim()
    const display = (label ?? target.split('|')[0]).trim()
    const slug = slugFromWikiTarget(target)
    return `[${display}](portolan://${encodeURIComponent(slug)})`
  })
  // LLM answers often cite as [label](slug) instead of [[slug]]
  out = out.replace(/\[([^\]]+)\]\(([a-z0-9][-a-z0-9_]*)\)/gi, (full, label, slug) => {
    if (full.includes('portolan://')) return full
    return `[${label}](portolan://${encodeURIComponent(String(slug).toLowerCase())})`
  })
  return out
}

export function stripFrontmatter(text: string): string {
  if (!text.startsWith('---')) return text
  const end = text.indexOf('---', 3)
  if (end === -1) return text
  return text.slice(end + 3).replace(/^\s*/, '')
}

export function prepareWikiMarkdown(text: string): string {
  return stripFrontmatter(text)
}

export function isChatModel(modelId: string): boolean {
  const low = modelId.toLowerCase()
  return !low.includes('embed') && !low.includes('nomic-embed')
}
