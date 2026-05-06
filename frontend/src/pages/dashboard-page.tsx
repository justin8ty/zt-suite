import { Navigate, useNavigate } from 'react-router-dom'

import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { useCurrentUser, useLogout } from '@/hooks/use-auth'
import { routes } from '@/lib/routes'
import { getApiErrorMessage } from '@/services/api-client'
import { useAuthStore } from '@/stores/auth-store'

export function DashboardPage() {
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const currentUser = useAuthStore((state) => state.currentUser)
  const userQuery = useCurrentUser()
  const logoutMutation = useLogout()

  if (!isAuthenticated) {
    return <Navigate replace to={routes.login} />
  }

  async function handleLogout() {
    await logoutMutation.mutateAsync()
    navigate(routes.login)
  }

  const user = userQuery.data ?? currentUser

  return (
    <main className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <div className="eyebrow">ZT Suite Dashboard</div>
          <h1>Security console</h1>
        </div>
        <button disabled={logoutMutation.isPending} onClick={handleLogout} type="button">
          {logoutMutation.isPending ? 'Signing out...' : 'Logout'}
        </button>
      </header>

      {userQuery.isLoading && <LoadingState message="Loading your profile..." />}
      {userQuery.isError && <ErrorState message={getApiErrorMessage(userQuery.error)} />}

      {user && (
        <section className="panel-grid">
          <article className="panel">
            <h2>Authenticated user</h2>
            <dl>
              <div>
                <dt>Email</dt>
                <dd>{user.email}</dd>
              </div>
              <div>
                <dt>MFA</dt>
                <dd>{user.mfa_enabled ? 'Enabled' : 'Not enabled'}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{user.is_active ? 'Active' : 'Inactive'}</dd>
              </div>
              <div>
                <dt>Roles</dt>
                <dd>{user.roles.map((role) => role.name).join(', ') || 'None'}</dd>
              </div>
            </dl>
          </article>

          <article className="panel">
            <h2>Next implementation phases</h2>
            <ul className="feature-list">
              <li>Dashboard metrics</li>
              <li>Device posture views</li>
              <li>Traffic and alert monitoring</li>
              <li>User and access-log management</li>
            </ul>
          </article>
        </section>
      )}
    </main>
  )
}
