interface StatusBadgeProps {
  children: string
  tone?: 'default' | 'success' | 'warning' | 'danger' | 'info'
}

const toneClassNames: Record<NonNullable<StatusBadgeProps['tone']>, string> = {
  default: 'border-zinc-950/10 bg-zinc-100 text-zinc-700',
  success: 'border-emerald-700/15 bg-emerald-50 text-emerald-800',
  warning: 'border-amber-700/15 bg-amber-50 text-amber-800',
  danger: 'border-red-700/15 bg-red-50 text-red-700',
  info: 'border-blue-700/15 bg-blue-50 text-blue-800',
}

export function StatusBadge({ children, tone = 'default' }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 font-mono text-[0.68rem] font-semibold uppercase tracking-[0.08em] ${toneClassNames[tone]}`}>
      {children}
    </span>
  )
}
