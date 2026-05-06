import { Navigate, Outlet } from 'react-router-dom'

import { routes } from '@/lib/routes'
import { useAuthStore } from '@/stores/auth-store'
import type { RoleName } from '@/types/user'

interface RequireRoleProps {
  allowedRoles: RoleName[]
}

export function RequireRole({ allowedRoles }: RequireRoleProps) {
  const currentUser = useAuthStore((state) => state.currentUser)
  const roles = currentUser?.roles.map((role) => role.name) ?? []
  const isAllowed = roles.some((role) => allowedRoles.includes(role as RoleName))

  if (!isAllowed) {
    return <Navigate replace to={routes.unauthorized} />
  }

  return <Outlet />
}
