import { Navigate, Route, Routes } from 'react-router-dom'

import { DashboardLayout } from '@/components/common/dashboard-layout'
import { RequireAuth } from '@/components/common/require-auth'
import { RequireRole } from '@/components/common/require-role'
import { AlertsPage } from '@/pages/alerts-page'
import { DashboardPage } from '@/pages/dashboard-page'
import { DeviceDetailPage } from '@/pages/device-detail-page'
import { DevicesPage } from '@/pages/devices-page'
import { LoginPage } from '@/pages/login-page'
import { FlowsPage } from '@/pages/flows-page'
import { LogsPage } from '@/pages/logs-page'
import { MfaPage } from '@/pages/mfa-page'
import { ProtectedFilesPage } from '@/pages/protected-files-page'
import { TrafficPage } from '@/pages/traffic-page'
import { UnauthorizedPage } from '@/pages/unauthorized-page'
import { UsersPage } from '@/pages/users-page'
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
          <Route element={<UnauthorizedPage />} path={routes.unauthorized} />
          <Route element={<ProtectedFilesPage />} path={routes.protectedFiles} />

          <Route element={<RequireRole allowedRoles={['admin', 'viewer']} />}>
            <Route element={<DevicesPage />} path={routes.devices} />
            <Route element={<DeviceDetailPage />} path={`${routes.devices}/:deviceId`} />
            <Route element={<TrafficPage />} path={routes.traffic} />
            <Route element={<FlowsPage />} path={routes.flows} />
            <Route element={<AlertsPage />} path={routes.alerts} />
          </Route>

          <Route element={<RequireRole allowedRoles={['admin']} />}>
            <Route element={<UsersPage />} path={routes.users} />
            <Route element={<LogsPage />} path={routes.logs} />
          </Route>
        </Route>
      </Route>

      <Route element={<Navigate replace to={routes.dashboard} />} path="*" />
    </Routes>
  )
}
