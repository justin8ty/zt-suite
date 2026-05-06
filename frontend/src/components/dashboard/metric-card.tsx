interface MetricCardProps {
  label: string
  value: string | number
  helper: string
  tone?: 'default' | 'success' | 'warning' | 'danger'
}

const toneClassNames: Record<NonNullable<MetricCardProps['tone']>, string> = {
  default: 'text-slate-50',
  success: 'text-green-200',
  warning: 'text-yellow-200',
  danger: 'text-red-300',
}

export function MetricCard({ label, value, helper, tone = 'default' }: MetricCardProps) {
  return (
    <article className="grid gap-2.5 rounded-3xl border border-slate-400/20 bg-slate-900/80 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl">
      <span className="text-sm text-slate-400">{label}</span>
      <strong className={`text-3xl leading-none font-bold tracking-tight md:text-4xl ${toneClassNames[tone]}`}>
        {value}
      </strong>
      <p className="text-sm text-slate-400">{helper}</p>
    </article>
  )
}
