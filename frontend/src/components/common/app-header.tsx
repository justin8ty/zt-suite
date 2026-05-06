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
    <header className="mb-5 flex items-center justify-between gap-6 rounded-3xl border border-slate-400/20 bg-slate-900/80 px-5 py-4 shadow-2xl shadow-black/30 backdrop-blur-xl max-md:flex-col max-md:items-stretch">
      <div>
        <div className="mb-2 text-xs font-extrabold tracking-[0.18em] text-cyan-300 uppercase">
          Zero-Trust Security Suite
        </div>
        <p className="text-slate-400">Identity, posture, traffic, and alert visibility.</p>
      </div>

      <div className="flex items-center gap-3 max-md:flex-col max-md:items-stretch">
        <div className="grid gap-0.5 text-right max-md:text-left">
          <span className="text-slate-50">{currentUser?.email ?? 'Authenticated user'}</span>
          <small className="text-slate-400">
            {currentUser?.roles.map((role) => role.name).join(', ') || 'no role'}
          </small>
        </div>
        <button
          className="min-h-11 rounded-xl bg-gradient-to-br from-sky-400 to-green-400 px-5 font-bold text-slate-950 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
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
