import { useNavigate } from 'react-router-dom'

import { useLogout } from '@/hooks/use-auth'
import { routes } from '@/lib/routes'
import { useAuthStore } from '@/stores/auth-store'

export function AppHeader() {
  const navigate = useNavigate()
  const currentUser = useAuthStore((state) => state.currentUser)
  const logoutMutation = useLogout()

  async function handleLogout() {
    await logoutMutation.mutateAsync()
    navigate(routes.login)
  }

  return (
    <header className="mb-4 flex items-center justify-between gap-4 rounded-2xl border border-zinc-950/10 bg-white px-5 py-3 shadow-[0_1px_3px_rgba(15,23,42,0.10)] max-md:flex-col max-md:items-stretch">
      <div>
        <div className="ui-eyebrow">Zero-trust security suite</div>
        <p className="mt-1 text-sm text-zinc-600">Identity, endpoint posture, network telemetry, and audit visibility.</p>
      </div>

      <div className="flex items-center gap-3 max-md:flex-col max-md:items-stretch">
        <div className="grid gap-0.5 text-right max-md:text-left">
          <span className="text-sm font-semibold text-zinc-950">{currentUser?.email ?? 'Authenticated user'}</span>
          <small className="font-mono text-[0.68rem] uppercase tracking-[0.12em] text-zinc-500">
            {currentUser?.roles.map((role) => role.name).join(', ') || 'no role'}
          </small>
        </div>
        <button
          className="ui-button-secondary"
          disabled={logoutMutation.isPending}
          onClick={handleLogout}
          type="button"
        >
          {logoutMutation.isPending ? 'Signing out...' : 'Logout'}
        </button>
      </div>
    </header>
  )
}
