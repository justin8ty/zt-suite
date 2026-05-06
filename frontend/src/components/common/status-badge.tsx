interface StatusBadgeProps {
  children: string
  tone?: 'default' | 'success' | 'warning' | 'danger' | 'info'
}

const toneClassNames: Record<NonNullable<StatusBadgeProps['tone']>, string> = {
  default: 'border-slate-400/25 bg-slate-500/10 text-slate-200',
  success: 'border-green-400/30 bg-green-500/10 text-green-200',
  warning: 'border-yellow-400/30 bg-yellow-500/10 text-yellow-200',
  danger: 'border-red-400/30 bg-red-500/10 text-red-200',
  info: 'border-sky-400/30 bg-sky-500/10 text-sky-200',
}

export function StatusBadge({ children, tone = 'default' }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-bold ${toneClassNames[tone]}`}>
      {children}
    </span>
  )
}
