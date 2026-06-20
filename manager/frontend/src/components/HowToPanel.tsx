import { HOW_TO_SECTIONS } from '../content/how-to'

function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    return <span key={i}>{part}</span>
  })
}

export function HowToPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null

  return (
    <div className="howto-overlay" role="dialog" aria-modal="true" aria-label="How to use SCUBA Ideaverse">
      <button type="button" className="howto-overlay__backdrop" aria-label="Close" onClick={onClose} />
      <aside className="howto-panel">
        <div className="howto-panel__head">
          <div>
            <h2 className="howto-panel__title">How to</h2>
            <p className="howto-panel__subtitle">SCUBA Ideaverse in five minutes</p>
          </div>
          <button type="button" className="icon-btn" onClick={onClose}>
            Close
          </button>
        </div>
        <div className="howto-panel__body">
          {HOW_TO_SECTIONS.map((section) => (
            <section key={section.id} className="howto-section">
              <h3 className="howto-section__title">{section.title}</h3>
              {'body' in section &&
                section.body?.map((line) => (
                  <p key={line} className="howto-section__p">
                    {renderInline(line)}
                  </p>
                ))}
              {'terms' in section &&
                section.terms?.map((t) => (
                  <dl key={t.name} className="howto-term">
                    <dt>{t.name}</dt>
                    <dd>{t.desc}</dd>
                  </dl>
                ))}
              {'links' in section && (
                <ul className="howto-links">
                  {section.links?.map((l) => (
                    <li key={l.href}>
                      <a href={l.href} target="_blank" rel="noreferrer">
                        {l.label} ↗
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ))}
        </div>
      </aside>
    </div>
  )
}
