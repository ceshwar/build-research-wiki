import { useMemo, useState } from 'react'
import type { ChartEntry, ChartTheme } from '../types'

export type FocusSelection = {
  papers: string[]
  themes: string[]
}

function toggle(list: string[], value: string) {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
}

export function QueryFocusPicker({
  entries,
  themes,
  selection,
  onChange,
  disabled,
}: {
  entries: ChartEntry[]
  themes: ChartTheme[]
  selection: FocusSelection
  onChange: (next: FocusSelection) => void
  disabled?: boolean
}) {
  const [query, setQuery] = useState('')
  const q = query.trim().toLowerCase()

  const groups = useMemo(() => {
    const byTheme = themes.map((theme) => {
      const papers = entries.filter((e) => e.themes?.includes(theme.slug))
      return { theme, papers }
    })
    const themedSlugs = new Set(
      byTheme.flatMap((g) => g.papers.map((p) => p.slug)),
    )
    const unthemed = entries.filter((e) => !themedSlugs.has(e.slug))
    return { byTheme, unthemed }
  }, [entries, themes])

  const filtered = useMemo(() => {
    if (!q) return groups
    const match = (s: string) => s.toLowerCase().includes(q)
    const byTheme = groups.byTheme
      .map(({ theme, papers }) => ({
        theme,
        papers: papers.filter(
          (p) => match(p.title) || match(p.slug) || match(theme.title),
        ),
      }))
      .filter(({ theme, papers }) => match(theme.title) || papers.length > 0)
    const unthemed = groups.unthemed.filter(
      (p) => match(p.title) || match(p.slug),
    )
    return { byTheme, unthemed }
  }, [groups, q])

  const selectedCount = selection.papers.length + selection.themes.length

  return (
    <div className="query-focus-panel">
      <div className="query-focus-panel__head">
        <input
          type="search"
          className="query-focus-panel__search"
          placeholder="Search themes or papers…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled}
        />
        {selectedCount > 0 && (
          <button
            type="button"
            className="query-focus-panel__clear"
            disabled={disabled}
            onClick={() => onChange({ papers: [], themes: [] })}
          >
            Clear ({selectedCount})
          </button>
        )}
      </div>

      <div className="query-focus-panel__tree">
        {filtered.byTheme.map(({ theme, papers }) => {
          const themeOn = selection.themes.includes(theme.slug)
          return (
            <div key={theme.slug} className="query-focus-panel__group">
              <label className="query-focus-panel__theme">
                <input
                  type="checkbox"
                  checked={themeOn}
                  disabled={disabled}
                  onChange={() =>
                    onChange({
                      ...selection,
                      themes: toggle(selection.themes, theme.slug),
                    })
                  }
                />
                <span>{theme.title}</span>
                <span className="query-focus-panel__count">{papers.length}</span>
              </label>
              {papers.length > 0 && (
                <ul className="query-focus-panel__papers">
                  {papers.map((p) => (
                    <li key={p.slug}>
                      <label className="query-focus-panel__paper">
                        <input
                          type="checkbox"
                          checked={selection.papers.includes(p.slug)}
                          disabled={disabled}
                          onChange={() =>
                            onChange({
                              ...selection,
                              papers: toggle(selection.papers, p.slug),
                            })
                          }
                        />
                        <span className="query-focus-panel__paper-title">{p.title}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
        {filtered.unthemed.length > 0 && (
          <div className="query-focus-panel__group">
            <div className="query-focus-panel__theme query-focus-panel__theme--muted">
              Other papers
            </div>
            <ul className="query-focus-panel__papers">
              {filtered.unthemed.map((p) => (
                <li key={p.slug}>
                  <label className="query-focus-panel__paper">
                    <input
                      type="checkbox"
                      checked={selection.papers.includes(p.slug)}
                      disabled={disabled}
                      onChange={() =>
                        onChange({
                          ...selection,
                          papers: toggle(selection.papers, p.slug),
                        })
                      }
                    />
                    <span className="query-focus-panel__paper-title">{p.title}</span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        )}
        {filtered.byTheme.length === 0 && filtered.unthemed.length === 0 && (
          <p className="query-focus-panel__empty">No matches.</p>
        )}
      </div>
    </div>
  )
}
