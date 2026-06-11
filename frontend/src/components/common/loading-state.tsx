interface LoadingStateProps {
  message?: string
}

export function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <div className="ui-panel flex items-center gap-3 text-sm text-zinc-600">
      <span className="size-2 rounded-full bg-zinc-400" />
      {message}
    </div>
  )
}
