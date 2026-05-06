import { Navigate, Route, Routes } from 'react-router-dom'

import { DashboardPage } from '@/pages/dashboard-page'
import { LoginPage } from '@/pages/login-page'
import { MfaPage } from '@/pages/mfa-page'
import { routes } from '@/lib/routes'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<Navigate replace to={routes.dashboard} />} path="/" />
      <Route element={<LoginPage />} path={routes.login} />
      <Route element={<MfaPage />} path={routes.mfa} />
      <Route element={<DashboardPage />} path={routes.dashboard} />
      <Route element={<Navigate replace to={routes.dashboard} />} path="*" />
    </Routes>
  )
}
