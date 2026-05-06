interface ErrorStateProps {
  title?: string
  message: string
}

export function ErrorState({ title = 'Something went wrong', message }: ErrorStateProps) {
  return (
    <div
      className="mb-5 grid gap-1 rounded-3xl border border-red-400/35 bg-slate-900/80 p-6 text-red-100 shadow-2xl shadow-black/30 backdrop-blur-xl"
      role="alert"
    >
      <strong className="text-red-100">{title}</strong>
      <span>{message}</span>
    </div>
  )
}
