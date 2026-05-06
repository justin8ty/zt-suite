interface PlaceholderPageProps {
  title: string
  description: string
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <main className="content-page">
      <div className="page-heading">
        <div className="eyebrow">Coming next</div>
        <h1>{title}</h1>
        <p className="muted">{description}</p>
      </div>
      <section className="panel">
        <h2>Planned implementation</h2>
        <p className="muted">
          This route is wired into the protected dashboard shell. The detailed table, filters,
          and actions will be implemented in the next frontend phases.
        </p>
      </section>
    </main>
  )
}
