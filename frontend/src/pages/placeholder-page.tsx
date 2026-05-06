interface PlaceholderPageProps {
  title: string
  description: string
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <main className="grid gap-5">
      <div className="px-1 py-2">
        <div className="mb-3.5 text-xs font-extrabold tracking-[0.18em] text-cyan-300 uppercase">
          Coming next
        </div>
        <h1 className="text-4xl leading-none font-bold tracking-tight text-slate-50 md:text-6xl">{title}</h1>
        <p className="mt-3.5 max-w-3xl text-slate-400">{description}</p>
      </div>
      <section className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
        <h2 className="text-lg font-bold text-slate-50">Planned implementation</h2>
        <p className="mt-4 text-slate-400">
          This route is wired into the protected dashboard shell. The detailed table, filters,
          and actions will be implemented in the next frontend phases.
        </p>
      </section>
    </main>
  )
}
