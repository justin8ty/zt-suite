interface ErrorStateProps {
  title?: string
  message: string
}

export function ErrorState({ title = 'We could not load this view', message }: ErrorStateProps) {
  return (
    <div
      className="mb-4 grid gap-1 rounded-2xl border border-red-700/15 bg-red-50 p-5 text-sm text-red-700"
      role="alert"
    >
      <strong className="font-semibold text-red-800">{title}</strong>
      <span>{message}</span>
    </div>
  )
}
