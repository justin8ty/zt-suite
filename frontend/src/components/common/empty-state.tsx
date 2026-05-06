interface EmptyStateProps {
  title: string
  message: string
}

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <section className="rounded-3xl border border-dashed border-slate-400/25 bg-slate-900/50 p-8 text-center shadow-2xl shadow-black/20 backdrop-blur-xl">
      <h2 className="text-lg font-bold text-slate-50">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-slate-400">{message}</p>
    </section>
  )
}
