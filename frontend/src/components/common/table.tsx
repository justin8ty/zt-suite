import type { ReactNode } from 'react'

interface TableCardProps {
  children: ReactNode
}

export function TableCard({ children }: TableCardProps) {
  return (
    <section className="overflow-hidden rounded-3xl border border-slate-400/20 bg-slate-900/80 shadow-2xl shadow-black/30 backdrop-blur-xl">
      <div className="overflow-x-auto">{children}</div>
    </section>
  )
}

export const tableClassName = 'min-w-full border-collapse text-left text-sm'
export const thClassName = 'border-b border-slate-400/15 px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-400'
export const tdClassName = 'border-b border-slate-400/10 px-4 py-4 text-slate-200'
