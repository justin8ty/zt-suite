interface PlaceholderPageProps {
  title: string
  description: string
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <main className="grid gap-5">
      <div className="px-1 py-2">
        <div className="ui-eyebrow mb-3">
          Coming next
        </div>
        <h1 className="text-4xl leading-none font-semibold tracking-tight text-zinc-950 md:text-6xl">{title}</h1>
        <p className="mt-3.5 max-w-3xl text-zinc-600">{description}</p>
      </div>
      <section className="ui-panel">
        <h2 className="text-lg font-semibold text-zinc-950">Planned implementation</h2>
        <p className="mt-4 text-zinc-600">
          This route is wired into the protected dashboard shell. The detailed table, filters,
          and actions will be implemented in the next frontend phases.
        </p>
      </section>
    </main>
  )
}
