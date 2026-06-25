import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchSettings, updateSettings } from '../api/client'
import type { AppSettings } from '../types'

function modelOptions(catalog: string[], current: string): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const id of [current, ...catalog]) {
    if (id && !seen.has(id)) {
      seen.add(id)
      out.push(id)
    }
  }
  return out
}

function ModelSelect({
  label,
  value,
  catalog,
  onChange,
}: {
  label: string
  value: string
  catalog: string[]
  onChange: (model: string) => void
}) {
  const options = modelOptions(catalog, value)
  return (
    <label className="settings-field">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((id) => (
          <option key={id} value={id}>
            {id}
          </option>
        ))}
      </select>
    </label>
  )
}

export function SettingsPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { data: s, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
    enabled: open,
  })

  const saveMutation = useMutation({
    mutationFn: (patch: Partial<AppSettings>) => updateSettings(patch),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings'] }),
  })

  if (!open) return null
  const llm = s?.llm
  const catalog = llm?.model_catalog ?? []

  const save = (patch: Partial<AppSettings>) => saveMutation.mutate(patch)

  const saveModel = (stage: 'deep_dive' | 'charting' | 'query', model: string) => {
    if (!llm) return
    save({ llm: { ...llm, models: { ...llm.models, [stage]: model } } })
  }

  return (
    <div className="settings-overlay" role="presentation" onClick={onClose}>
      <div
        className="settings-panel"
        role="dialog"
        aria-label="Settings"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="settings-panel__header">
          <h2>Settings</h2>
          <button type="button" className="settings-panel__close" onClick={onClose}>
            ×
          </button>
        </header>
        {isLoading && <p className="p-4 text-sm text-[var(--muted)]">Loading…</p>}
        {s && llm && (
          <div className="settings-panel__body">
            <section>
              <h3>Viewer</h3>
              <label className="settings-field">
                <span>Open papers in</span>
                <select
                  value={s.view_in}
                  onChange={(e) => save({ view_in: e.target.value as 'app' | 'obsidian' })}
                >
                  <option value="app">Portolan (in-app)</option>
                  <option value="obsidian">Obsidian</option>
                </select>
              </label>
            </section>
            <section>
              <h3>Local LLM (Ollama)</h3>
              <label className="settings-field">
                <span>Ollama URL</span>
                <input
                  type="url"
                  defaultValue={llm.ollama_url}
                  onBlur={(e) => save({ llm: { ...llm, ollama_url: e.target.value } })}
                />
              </label>
              <p className="settings-hint">GPU tunnel: http://127.0.0.1:11500</p>
              <ModelSelect
                label="Deep Dive model"
                value={llm.models.deep_dive}
                catalog={catalog}
                onChange={(model) => saveModel('deep_dive', model)}
              />
              <ModelSelect
                label="Charting model"
                value={llm.models.charting}
                catalog={catalog}
                onChange={(model) => saveModel('charting', model)}
              />
              <ModelSelect
                label="Query model"
                value={llm.models.query}
                catalog={catalog}
                onChange={(model) => saveModel('query', model)}
              />
            </section>
            <section>
              <h3>Deep Dive provider</h3>
              <label className="settings-field">
                <span>Use</span>
                <select
                  value={llm.deep_dive_provider}
                  onChange={(e) => save({ llm: { ...llm, deep_dive_provider: e.target.value } })}
                >
                  <option value="local">Local Ollama</option>
                  <option value="frontier">Frontier API</option>
                </select>
              </label>
              {llm.deep_dive_provider === 'frontier' && (
                <>
                  <label className="settings-field">
                    <span>Frontier provider</span>
                    <select
                      value={llm.frontier.provider}
                      onChange={(e) =>
                        save({
                          llm: { ...llm, frontier: { ...llm.frontier, provider: e.target.value } },
                        })
                      }
                    >
                      <option value="anthropic">Anthropic</option>
                      <option value="openai">OpenAI</option>
                    </select>
                  </label>
                  <label className="settings-field">
                    <span>Frontier model</span>
                    <input
                      type="text"
                      defaultValue={llm.frontier.deep_dive_model}
                      onBlur={(e) =>
                        save({
                          llm: {
                            ...llm,
                            frontier: { ...llm.frontier, deep_dive_model: e.target.value },
                          },
                        })
                      }
                    />
                  </label>
                  <p className="settings-hint">
                    Set <code>ANTHROPIC_API_KEY</code> or <code>OPENAI_API_KEY</code> in your environment.
                  </p>
                </>
              )}
            </section>
            <section>
              <h3>Query provider</h3>
              <label className="settings-field">
                <span>Use</span>
                <select
                  value={llm.query_provider}
                  onChange={(e) => save({ llm: { ...llm, query_provider: e.target.value } })}
                >
                  <option value="local">Local Ollama</option>
                  <option value="frontier">Frontier API</option>
                </select>
              </label>
            </section>
            {saveMutation.isError && (
              <p className="text-red-400 text-xs">{saveMutation.error.message}</p>
            )}
            {saveMutation.isSuccess && <p className="text-[var(--success)] text-xs">Saved.</p>}
          </div>
        )}
      </div>
    </div>
  )
}
