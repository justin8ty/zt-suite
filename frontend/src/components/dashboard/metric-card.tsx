interface MetricCardProps {
  label: string
  value: string | number
  helper: string
  tone?: 'default' | 'success' | 'warning' | 'danger'
}

const toneClassNames: Record<NonNullable<MetricCardProps['tone']>, string> = {
  default: 'text-zinc-950',
  success: 'text-emerald-700',
  warning: 'text-amber-700',
  danger: 'text-red-700',
}

export function MetricCard({ label, value, helper, tone = 'default' }: MetricCardProps) {
  return (
    <article className="ui-panel ui-card-hover grid gap-2.5">
      <span className="font-mono text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-zinc-500">{label}</span>
      <strong className={`text-3xl leading-none font-semibold tracking-[-0.022em] tabular-nums md:text-4xl ${toneClassNames[tone]}`}>
        {value}
      </strong>
      <p className="text-sm leading-5 text-zinc-600">{helper}</p>
    </article>
  )
}
