interface EmptyStateProps {
  title: string
  message: string
}

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <section className="rounded-2xl border border-dashed border-zinc-950/15 bg-zinc-50/80 p-8 text-center">
      <h2 className="ui-section-title">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-zinc-600">{message}</p>
    </section>
  )
}
