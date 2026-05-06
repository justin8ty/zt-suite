interface LoadingStateProps {
  message?: string
}

export function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <div className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-6 text-slate-200 shadow-2xl shadow-black/30 backdrop-blur-xl">
      {message}
    </div>
  )
}
