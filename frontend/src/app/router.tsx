import { Navigate, Route, Routes } from 'react-router-dom'

import { DashboardLayout } from '@/components/common/dashboard-layout'
import { RequireAuth } from '@/components/common/require-auth'
import { DashboardPage } from '@/pages/dashboard-page'
import { LoginPage } from '@/pages/login-page'
import { MfaPage } from '@/pages/mfa-page'
import { PlaceholderPage } from '@/pages/placeholder-page'
import { routes } from '@/lib/routes'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<Navigate replace to={routes.dashboard} />} path="/" />
      <Route element={<LoginPage />} path={routes.login} />
      <Route element={<MfaPage />} path={routes.mfa} />

      <Route element={<RequireAuth />}>
        <Route element={<DashboardLayout />}>
          <Route element={<DashboardPage />} path={routes.dashboard} />
          <Route
            element={
              <PlaceholderPage
                description="Review registered endpoints, compliance status, owners, and latest posture."
                title="Devices"
              />
            }
            path={routes.devices}
          />
          <Route
            element={
              <PlaceholderPage
                description="Inspect network traffic metadata uploaded by endpoint agents."
                title="Traffic"
              />
            }
            path={routes.traffic}
          />
          <Route
            element={
              <PlaceholderPage
                description="Triage reported anomalies and acknowledge security alerts."
                title="Alerts"
              />
            }
            path={routes.alerts}
          />
          <Route
            element={
              <PlaceholderPage
                description="Manage users, MFA status, active state, and role assignment."
                title="Users"
              />
            }
            path={routes.users}
          />
          <Route
            element={
              <PlaceholderPage
                description="Audit authentication, authorization, and protected resource access events."
                title="Access Logs"
              />
            }
            path={routes.logs}
          />
          <Route
            element={
              <PlaceholderPage
                description="Demonstrate the full Zero-Trust access chain with MFA, RBAC, and compliant devices."
                title="Protected Files"
              />
            }
            path={routes.protectedFiles}
          />
        </Route>
      </Route>

      <Route element={<Navigate replace to={routes.dashboard} />} path="*" />
    </Routes>
  )
}
