import type { ReactNode } from 'react'

interface PageShellProps {
  eyebrow: string
  title: string
  description: string
  children: ReactNode
  actions?: ReactNode
}

export function PageShell({ eyebrow, title, description, children, actions }: PageShellProps) {
  return (
    <main className="grid gap-4" id="main-content">
      <div className="flex items-end justify-between gap-4 px-1 py-2 max-md:flex-col max-md:items-start">
        <div>
          <div className="ui-eyebrow mb-3">{eyebrow}</div>
          <h1 className="ui-title">{title}</h1>
          <p className="ui-subtitle">{description}</p>
        </div>
        {actions}
      </div>
      {children}
    </main>
  )
}
