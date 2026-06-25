import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { fetchQueryResult, fetchSettings, runWikiQuery } from '../api/client'
import { MarkdownViewer } from './MarkdownViewer'

type QueryMeta = { model: string; elapsed_s?: number }

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

export function QueryPanel({
  vaultId,
  onJobStart,
  onQueryMeta,
}: {
  vaultId: string
  onJobStart: (jobId: string) => void
  onQueryMeta?: (meta: QueryMeta | null) => void
}) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [queryModel, setQueryModel] = useState('')
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

  const queryMutation = useMutation({
    mutationFn: (q: string) => runWikiQuery(vaultId, q, undefined, activeModel),
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
              elapsed_s: res.elapsed_s ?? (startedAt ? Math.round((Date.now() - startedAt) / 100) / 10 : undefined),
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
    if (q && !busy) queryMutation.mutate(q)
  }

  return (
    <div className="query-panel">
      <p className="workspace-panel__meta">
        Ask questions against your charted wiki. Answers cite sources from your papers. Unreviewed
        LLM Deep Dives are included — weigh claims carefully.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
        className="query-form"
      >
        <label className="query-form__label">
          <span>Model</span>
          <select
            className="query-form__model"
            value={activeModel}
            onChange={(e) => setQueryModel(e.target.value)}
            disabled={busy}
          >
            {modelOptions(catalog, defaultModel).map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </label>
        <textarea
          className="query-form__input"
          rows={3}
          placeholder="e.g. What does the literature say about toxic comments and feed ranking?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={busy}
        />
        <div className="query-form__actions">
          <button type="submit" className="btn-primary px-4 py-2 text-sm" disabled={busy || !question.trim()}>
            Ask wiki
          </button>
          {busy && (
            <span className="query-form__status" role="status">
              <span className="spinner spinner--sm" aria-hidden="true" />
              Working on your answer…
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
              </span>
            )}
          </div>
          <MarkdownViewer content={answer} className="query-answer__body" />
        </div>
      )}
    </div>
  )
}
