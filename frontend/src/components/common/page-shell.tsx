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
    <main className="grid gap-5">
      <div className="flex items-end justify-between gap-4 px-1 py-2 max-md:flex-col max-md:items-start">
        <div>
          <div className="mb-3.5 text-xs font-extrabold tracking-[0.18em] text-cyan-300 uppercase">
            {eyebrow}
          </div>
          <h1 className="text-4xl leading-none font-bold tracking-tight text-slate-50 md:text-6xl">
            {title}
          </h1>
          <p className="mt-3.5 max-w-3xl text-slate-400">{description}</p>
        </div>
        {actions}
      </div>
      {children}
    </main>
  )
}
