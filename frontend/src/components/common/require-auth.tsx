import { useEffect, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { routes } from '@/lib/routes'
import { authService } from '@/services/auth-service'
import { useAuthStore } from '@/stores/auth-store'

export function RequireAuth() {
  const location = useLocation()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const setTokens = useAuthStore((state) => state.setTokens)
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const [isRestoringSession, setIsRestoringSession] = useState(!isAuthenticated)

  useEffect(() => {
    let isActive = true

    if (isAuthenticated) {
      setIsRestoringSession(false)
      return () => {
        isActive = false
      }
    }

    authService
      .refresh()
      .then((tokens) => {
        if (!isActive) return
        setTokens(tokens)
        setIsRestoringSession(false)
      })
      .catch(() => {
        if (!isActive) return
        clearAuth()
        setIsRestoringSession(false)
      })

    return () => {
      isActive = false
    }
  }, [clearAuth, isAuthenticated, setTokens])

  if (isRestoringSession) {
    return <div className="grid min-h-screen place-items-center text-slate-300">Restoring session...</div>
  }

  if (!isAuthenticated) {
    return <Navigate replace state={{ from: location }} to={routes.login} />
  }

  return <Outlet />
}
