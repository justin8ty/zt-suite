import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { routes } from '@/lib/routes'
import { useAuthStore } from '@/stores/auth-store'

export function RequireAuth() {
  const location = useLocation()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate replace state={{ from: location }} to={routes.login} />
  }

  return <Outlet />
}
