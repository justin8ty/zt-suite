import { useAuthStore } from '@/stores/auth-store'
import type { RoleName } from '@/types/user'

export function useRole() {
  const currentUser = useAuthStore((state) => state.currentUser)
  const roles = currentUser?.roles.map((role) => role.name) ?? []

  function hasRole(...allowedRoles: RoleName[]): boolean {
    return roles.some((role) => allowedRoles.includes(role as RoleName))
  }

  return {
    roles,
    isAdmin: hasRole('admin'),
    isViewer: hasRole('viewer'),
    isUser: hasRole('user'),
    canViewSecurityData: hasRole('admin', 'viewer'),
    hasRole,
  }
}
