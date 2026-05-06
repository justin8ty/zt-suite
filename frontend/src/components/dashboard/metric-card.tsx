interface MetricCardProps {
  label: string
  value: string | number
  helper: string
  tone?: 'default' | 'success' | 'warning' | 'danger'
}

export function MetricCard({ label, value, helper, tone = 'default' }: MetricCardProps) {
  return (
    <article className={`metric-card metric-card-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </article>
  )
}
