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
    <header className="app-header">
      <div>
        <div className="eyebrow">Zero-Trust Security Suite</div>
        <p className="header-subtitle">Identity, posture, traffic, and alert visibility.</p>
      </div>

      <div className="header-actions">
        <div className="user-chip">
          <span>{currentUser?.email ?? 'Authenticated user'}</span>
          <small>{currentUser?.roles.map((role) => role.name).join(', ') || 'no role'}</small>
        </div>
        <button disabled={logoutMutation.isPending} onClick={handleLogout} type="button">
          {logoutMutation.isPending ? 'Signing out...' : 'Logout'}
        </button>
      </div>
    </header>
  )
}
