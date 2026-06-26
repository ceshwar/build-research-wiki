import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { fetchQueryResult, fetchSettings, runWikiQuery } from '../api/client'
import type { ChartEntry, ChartTheme } from '../types'
import { isChatModel, resolveWikiPath, type WikiPathResolver } from '../lib/wikiLinks'
import { MarkdownViewer } from './MarkdownViewer'
import { QueryFocusPicker, type FocusSelection } from './QueryFocusPicker'

type QueryMeta = { model: string; elapsed_s?: number; sources_used?: string[] }
type TrustScope = 'all' | 'verified' | 'needs_review' | 'uncharted'
type ScopeMode = TrustScope | 'focused'

function chatModelOptions(catalog: string[], current: string): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const id of [current, ...catalog]) {
    if (id && isChatModel(id) && !seen.has(id)) {
      seen.add(id)
      out.push(id)
    }
  }
  return out
}

export function QueryPanel({
  vaultId,
  wikiResolver,
  chartEntries = [],
  themeOptions = [],
  onJobStart,
  onQueryMeta,
  onWikiNavigate,
}: {
  vaultId: string
  wikiResolver?: WikiPathResolver
  chartEntries?: ChartEntry[]
  themeOptions?: ChartTheme[]
  onJobStart: (jobId: string) => void
  onQueryMeta?: (meta: QueryMeta | null) => void
  onWikiNavigate?: (path: string, title: string) => void
}) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [queryModel, setQueryModel] = useState('')
  const [scopeMode, setScopeMode] = useState<ScopeMode>('all')
  const [trustScope, setTrustScope] = useState<TrustScope>('all')
  const [focus, setFocus] = useState<FocusSelection>({ papers: [], themes: [] })
  const [pdfFallback, setPdfFallback] = useState(true)
  const [pendingJobId, setPendingJobId] = useState<string | null>(null)
  const [answerMeta, setAnswerMeta] = useState<QueryMeta | null>(null)
  const [startedAt, setStartedAt] = useState<number | null>(null)

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  })

  const catalog = settings?.llm.model_catalog ?? []
  const defaultModel = settings?.llm.models.query ?? 'qwen3:32b'
  const activeModel = queryModel || defaultModel
  const modelChoices = useMemo(() => chatModelOptions(catalog, defaultModel), [catalog, defaultModel])

  const isFocused = scopeMode === 'focused'
  const focusCount = focus.papers.length + focus.themes.length
  const canSubmit =
    question.trim().length > 0 && (!isFocused || focusCount > 0)

  const queryMutation = useMutation({
    mutationFn: (q: string) =>
      runWikiQuery(
        vaultId,
        q,
        undefined,
        activeModel,
        isFocused ? trustScope : scopeMode,
        isFocused ? focus.papers : [],
        isFocused ? focus.themes : [],
        pdfFallback,
      ),
    onSuccess: (data) => {
      setPendingJobId(data.job_id)
      onJobStart(data.job_id)
      setAnswer('')
      setAnswerMeta(null)
      onQueryMeta?.(null)
      setStartedAt(Date.now())
    },
  })

  useEffect(() => {
    if (!pendingJobId) return
    let cancelled = false
    const poll = async () => {
      for (let i = 0; i < 180; i++) {
        if (cancelled) return
        try {
          const res = await fetchQueryResult(pendingJobId, question)
          if (res.status === 'completed') {
            const meta: QueryMeta = {
              model: res.model || activeModel,
              elapsed_s:
                res.elapsed_s ??
                (startedAt ? Math.round((Date.now() - startedAt) / 100) / 10 : undefined),
              sources_used: res.sources_used,
            }
            setAnswer(res.answer)
            setAnswerMeta(meta)
            onQueryMeta?.(meta)
            setPendingJobId(null)
            setStartedAt(null)
            return
          }
          if (res.status === 'failed') {
            setPendingJobId(null)
            setStartedAt(null)
            onQueryMeta?.(null)
            return
          }
        } catch {
          /* retry */
        }
        await new Promise((r) => setTimeout(r, 1000))
      }
      setPendingJobId(null)
      setStartedAt(null)
      onQueryMeta?.(null)
    }
    poll()
    return () => {
      cancelled = true
    }
  }, [pendingJobId, question, activeModel, onQueryMeta, startedAt])

  const busy = queryMutation.isPending || !!pendingJobId

  const submit = () => {
    const q = question.trim()
    if (q && canSubmit && !busy) queryMutation.mutate(q)
  }

  const onWikiLink = onWikiNavigate
    ? (slug: string, label: string) => {
        const entry = chartEntries.find((e) => e.slug === slug)
        const path = resolveWikiPath(slug, wikiResolver)
        onWikiNavigate(path, entry?.title ?? label)
      }
    : undefined

  const hasPicker = chartEntries.length > 0 || themeOptions.length > 0

  return (
    <div className="query-panel">
      <p className="workspace-panel__meta">
        Answers use <strong>chart wiki pages</strong> (abstracts, deep dives, themes). Citations are{' '}
        <code>[[wikilinks]]</code> to those pages. Optional PDF excerpts fill in when chart text is
        thin.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
        className="query-form"
      >
        <div className="query-form__row">
          <label className="query-form__label">
            <span>Model</span>
            <select
              className="query-form__model"
              value={activeModel}
              onChange={(e) => setQueryModel(e.target.value)}
              disabled={busy}
            >
              {modelChoices.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </label>
          <label className="query-form__label">
            <span>Scope</span>
            <select
              className="query-form__model"
              value={scopeMode}
              onChange={(e) => setScopeMode(e.target.value as ScopeMode)}
              disabled={busy}
            >
              <option value="all">All charted papers</option>
              <option value="verified">Deep dive only</option>
              <option value="needs_review">Quick dip only</option>
              <option value="uncharted">Uncharted only</option>
              <option value="focused">Focused — pick papers/themes…</option>
            </select>
          </label>
        </div>

        {isFocused && hasPicker && (
          <div className="query-focused-block">
            <div className="query-focused-block__head">
              <label className="query-form__label query-focused-block__trust">
                <span>Trust filter</span>
                <select
                  className="query-form__model"
                  value={trustScope}
                  onChange={(e) => setTrustScope(e.target.value as TrustScope)}
                  disabled={busy}
                >
                  <option value="all">Any tier</option>
                  <option value="verified">Deep dive</option>
                  <option value="needs_review">Quick dip</option>
                  <option value="uncharted">Uncharted</option>
                </select>
              </label>
              <label className="query-focused-block__pdf">
                <input
                  type="checkbox"
                  checked={pdfFallback}
                  disabled={busy}
                  onChange={(e) => setPdfFallback(e.target.checked)}
                />
                PDF excerpt fallback when chart text is thin
              </label>
            </div>
            <QueryFocusPicker
              entries={chartEntries}
              themes={themeOptions}
              selection={focus}
              onChange={setFocus}
              disabled={busy}
            />
            {focusCount === 0 && (
              <p className="query-focused-block__hint">Select at least one theme or paper.</p>
            )}
          </div>
        )}

        {!isFocused && (
          <label className="query-focused-block__pdf query-focused-block__pdf--inline">
            <input
              type="checkbox"
              checked={pdfFallback}
              disabled={busy}
              onChange={(e) => setPdfFallback(e.target.checked)}
            />
            PDF excerpt fallback when chart text is thin
          </label>
        )}

        <textarea
          className="query-form__input"
          rows={3}
          placeholder="e.g. What does the literature say about toxic comments and feed ranking?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={busy}
        />
        <div className="query-form__actions">
          <button
            type="submit"
            className="btn-primary px-4 py-2 text-sm"
            disabled={busy || !canSubmit}
          >
            Ask wiki
          </button>
          {busy && (
            <span className="query-form__status" role="status">
              <span className="spinner spinner--sm" aria-hidden="true" />
              Reading chart{pdfFallback ? ' + PDF excerpts' : ''}…
            </span>
          )}
        </div>
      </form>
      {queryMutation.isError && (
        <p className="mt-2 text-xs text-red-400">{queryMutation.error.message}</p>
      )}
      {answer && (
        <div className="query-answer">
          <div className="query-answer__head">
            <h3>Answer</h3>
            {answerMeta && (
              <span className="query-answer__meta">
                {answerMeta.model}
                {answerMeta.elapsed_s != null ? ` · ${answerMeta.elapsed_s}s` : ''}
                {answerMeta.sources_used && answerMeta.sources_used.length > 0 && (
                  <> · {answerMeta.sources_used.length} source(s)</>
                )}
              </span>
            )}
          </div>
          <MarkdownViewer content={answer} className="query-answer__body" onWikiLink={onWikiLink} />
        </div>
      )}
    </div>
  )
}
