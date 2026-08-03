import type { Overview } from '../types'

type SummaryCardsProps = {
  overview?: Overview
  loading: boolean
}

const cards = [
  { key: 'incidents', label: 'Incidents', tone: 'blue', suffix: '' },
  { key: 'critical_incidents', label: 'Critical', tone: 'red', suffix: '' },
  { key: 'affected_sensors', label: 'Affected sensors', tone: 'amber', suffix: '' },
  { key: 'anomaly_rate_pct', label: 'Anomaly rate', tone: 'slate', suffix: '%' },
] as const

export function SummaryCards({ overview, loading }: SummaryCardsProps) {
  return (
    <section className="summary-grid" aria-label="Anomaly overview">
      {cards.map((card) => (
        <article className={`summary-card summary-card--${card.tone}`} key={card.key}>
          <div className="summary-card__topline">
            <span>{card.label}</span>
            <span className="summary-card__dot" aria-hidden="true" />
          </div>
          {loading ? (
            <div className="skeleton skeleton--value" />
          ) : (
            <strong>{overview?.[card.key] ?? 0}{card.suffix}</strong>
          )}
          <p>{card.key === 'anomaly_rate_pct' ? 'Flagged observations in view' : 'Within selected filters'}</p>
        </article>
      ))}
    </section>
  )
}

