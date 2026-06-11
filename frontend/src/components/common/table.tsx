import type { ReactNode } from 'react'

interface TableCardProps {
  children: ReactNode
}

export function TableCard({ children }: TableCardProps) {
  return (
    <section className="ui-table-card">
      <div className="overflow-x-auto">{children}</div>
    </section>
  )
}

export const tableClassName = 'ui-table'
export const thClassName = 'ui-th'
export const tdClassName = 'ui-td'
