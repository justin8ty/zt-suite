interface ErrorStateProps {
  title?: string
  message: string
}

export function ErrorState({ title = 'Something went wrong', message }: ErrorStateProps) {
  return (
    <div className="alert alert-error" role="alert">
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  )
}
