import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import {
  buildWikiResolver,
  expandWikilinks,
  extractWikilinkSlugs,
  parseWikiLinkHref,
  prepareWikiMarkdown,
  resolveWikiPath,
  slugFromWikiTarget,
  wikiPathForSlug,
} from './wikiLinks'

const REPO_ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '../../../..')
const MINIMAL_VAULT = join(REPO_ROOT, 'examples/minimal-vault')

function scanVaultWikiResolver(vaultRoot: string) {
  const nodes: { slug: string; wiki_page: string; type: string }[] = []
  const wikiRoot = join(vaultRoot, 'wiki')
  const folders: Record<string, string> = {
    papers: 'paper',
    themes: 'theme',
    concepts: 'concept',
    entities: 'entity',
    sources: 'source',
  }
  for (const [folder, type] of Object.entries(folders)) {
    const dir = join(wikiRoot, folder)
    if (!existsSync(dir)) continue
    for (const name of readdirSync(dir)) {
      if (!name.endsWith('.md')) continue
      const slug = name.replace(/\.md$/i, '')
      nodes.push({
        slug,
        type,
        wiki_page: relative(vaultRoot, join(dir, name)).replace(/\\/g, '/'),
      })
    }
  }
  return buildWikiResolver([], nodes)
}

describe('parseWikiLinkHref', () => {
  it('parses portolan:// slugs', () => {
    expect(parseWikiLinkHref('portolan://language-of-approval')).toBe('language-of-approval')
    expect(parseWikiLinkHref('portolan://wiki%2Fpapers%2Ffoo.md')).toBe('foo')
  })

  it('parses wiki/… vault paths', () => {
    expect(parseWikiLinkHref('wiki/papers/language-of-approval.md')).toBe('language-of-approval')
    expect(parseWikiLinkHref('/wiki/themes/algorithmic-ai-audits')).toBe('algorithmic-ai-audits')
    expect(parseWikiLinkHref('wiki/concepts/policy-practice-gap.md#section')).toBe(
      'policy-practice-gap',
    )
  })

  it('parses bare slug hrefs from LLM markdown citations', () => {
    expect(parseWikiLinkHref('language-of-approval')).toBe('language-of-approval')
    expect(parseWikiLinkHref('/positive-reinforcement-reddit')).toBe('positive-reinforcement-reddit')
  })

  it('ignores external and empty hrefs', () => {
    expect(parseWikiLinkHref('https://example.com/paper')).toBeNull()
    expect(parseWikiLinkHref('mailto:you@example.com')).toBeNull()
    expect(parseWikiLinkHref('')).toBeNull()
    expect(parseWikiLinkHref(null)).toBeNull()
  })
})

describe('slugFromWikiTarget', () => {
  it('strips display labels, paths, extensions, and anchors', () => {
    expect(slugFromWikiTarget('causal-inference-observational|Selection-on-observables')).toBe(
      'causal-inference-observational',
    )
    expect(slugFromWikiTarget('wiki/concepts/policy-practice-gap.md')).toBe('policy-practice-gap')
    expect(slugFromWikiTarget('positive-reinforcement#claims')).toBe('positive-reinforcement')
  })
})

describe('expandWikilinks', () => {
  it('converts Obsidian wikilinks to portolan markdown links', () => {
    expect(expandWikilinks('See [[language-of-approval]] for details.')).toBe(
      'See [language-of-approval](portolan://language-of-approval) for details.',
    )
    expect(expandWikilinks('[[language-of-approval|Language of Approval]]')).toBe(
      '[Language of Approval](portolan://language-of-approval)',
    )
    expect(
      expandWikilinks(
        '**[[causal-inference-observational|Selection-on-observables causal inference]]**',
      ),
    ).toBe(
      '**[Selection-on-observables causal inference](portolan://causal-inference-observational)**',
    )
  })

  it('converts bare [label](slug) citations from query answers', () => {
    expect(expandWikilinks('Cited in [Language of Approval](language-of-approval).')).toBe(
      'Cited in [Language of Approval](portolan://language-of-approval).',
    )
  })

  it('does not rewrite already-expanded portolan links', () => {
    const once = expandWikilinks('[[foo-bar]]')
    expect(expandWikilinks(once)).toBe(once)
  })
})

describe('resolveWikiPath', () => {
  it('prefers chart map paths over folder hints', () => {
    const path = resolveWikiPath('custom-slug', {
      pathsBySlug: { 'custom-slug': 'wiki/sources/2026-01-01-custom.md' },
      hints: { papers: ['custom-slug'] },
    })
    expect(path).toBe('wiki/sources/2026-01-01-custom.md')
  })

  it('uses hint folders when no chart path exists', () => {
    expect(
      wikiPathForSlug('algorithmic-ai-audits', { themes: ['algorithmic-ai-audits'] }),
    ).toBe('wiki/themes/algorithmic-ai-audits.md')
    expect(
      resolveWikiPath('language-of-approval', {
        hints: { papers: ['language-of-approval'] },
      }),
    ).toBe('wiki/papers/language-of-approval.md')
  })

  it('resolves concept slugs from graph registry paths', () => {
    const resolver = buildWikiResolver([], [
      {
        slug: 'policy-practice-gap',
        type: 'concept',
        wiki_page: 'wiki/concepts/policy-practice-gap.md',
      },
    ])
    expect(resolveWikiPath('policy-practice-gap', resolver)).toBe(
      'wiki/concepts/policy-practice-gap.md',
    )
  })
})

describe('prepareWikiMarkdown', () => {
  it('strips YAML frontmatter before rendering', () => {
    const raw = `---
type: paper
title: Example
---

# Example

[[policy-practice-gap]]`
    expect(prepareWikiMarkdown(raw)).toBe('# Example\n\n[[policy-practice-gap]]')
  })
})

describe('minimal-vault paper wikilinks', () => {
  const resolver = scanVaultWikiResolver(MINIMAL_VAULT)
  const paperDir = join(MINIMAL_VAULT, 'wiki/papers')

  it('resolves every wikilink in charted paper notes to an existing wiki file', () => {
    const paperFiles = readdirSync(paperDir).filter((f) => f.endsWith('.md'))
    expect(paperFiles.length).toBeGreaterThan(0)

    const unresolved: string[] = []
    for (const file of paperFiles) {
      const raw = readFileSync(join(paperDir, file), 'utf8')
      const body = prepareWikiMarkdown(raw)
      for (const slug of extractWikilinkSlugs(body)) {
        const path = resolveWikiPath(slug, resolver)
        if (!existsSync(join(MINIMAL_VAULT, path))) {
          unresolved.push(`${file}: [[${slug}]] → ${path}`)
        }
      }
    }
    expect(unresolved).toEqual([])
  })

  it('expands paper wikilinks to clickable portolan hrefs', () => {
    const raw = readFileSync(join(paperDir, 'language-of-approval.md'), 'utf8')
    const body = prepareWikiMarkdown(raw)
    const expanded = expandWikilinks(body)
    for (const slug of extractWikilinkSlugs(body)) {
      expect(expanded).toContain(`portolan://${slug}`)
      expect(parseWikiLinkHref(`portolan://${slug}`)).toBe(slug)
    }
  })
})
