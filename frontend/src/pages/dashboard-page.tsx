import { useQuery } from '@tanstack/react-query'

import { MetricCard } from '@/components/dashboard/metric-card'
import { ErrorState } from '@/components/common/error-state'
import { useRole } from '@/hooks/use-role'
import { alertService } from '@/services/alert-service'
import { deviceService } from '@/services/device-service'
import { getApiErrorMessage } from '@/services/api-client'
import { logService } from '@/services/log-service'
import { trafficService } from '@/services/traffic-service'
import { useAuthStore } from '@/stores/auth-store'

const DASHBOARD_REFETCH_MS = 10_000

export function DashboardPage() {
  const currentUser = useAuthStore((state) => state.currentUser)
  const { isAdmin, canViewSecurityData } = useRole()

  const devicesQuery = useQuery({
    queryKey: ['dashboard', 'devices'],
    queryFn: () => deviceService.list({ limit: 100 }),
    enabled: canViewSecurityData,
    refetchInterval: DASHBOARD_REFETCH_MS,
  })

  const openAlertsQuery = useQuery({
    queryKey: ['dashboard', 'open-alerts'],
    queryFn: () => alertService.list({ limit: 100, is_acknowledged: false }),
    enabled: canViewSecurityData,
    refetchInterval: DASHBOARD_REFETCH_MS,
  })

  const trafficQuery = useQuery({
    queryKey: ['dashboard', 'traffic'],
    queryFn: () => trafficService.list({ limit: 100 }),
    enabled: canViewSecurityData,
    refetchInterval: DASHBOARD_REFETCH_MS,
  })

  const logsQuery = useQuery({
    queryKey: ['dashboard', 'access-failures'],
    queryFn: () => logService.list({ limit: 100 }),
    enabled: isAdmin,
    refetchInterval: DASHBOARD_REFETCH_MS,
  })

  const devices = devicesQuery.data?.devices ?? []
  const alerts = openAlertsQuery.data ?? []
  const traffic = trafficQuery.data ?? []
  const logs = logsQuery.data?.logs ?? []

  const compliantDevices = devices.filter((device) => device.is_compliant).length
  const highRiskAlerts = alerts.filter((alert) =>
    ['critical', 'high'].includes(alert.severity.toLowerCase()),
  ).length
  const accessFailures = logs.filter((log) => log.status === 'failure').length

  return (
    <main className="content-page">
      <div className="page-heading">
        <div className="eyebrow">Live overview</div>
        <h1>Security dashboard</h1>
        <p className="muted">
          Welcome{currentUser ? `, ${currentUser.email}` : ''}. Dashboard data refreshes every
          10 seconds where your role permits access.
        </p>
      </div>

      {!canViewSecurityData && (
        <ErrorState
          title="Limited dashboard access"
          message="Your role can access protected app features, but security metrics require admin or viewer role."
        />
      )}

      <section className="metrics-grid" aria-label="Security metrics">
        <MetricCard
          helper={canViewSecurityData ? `${compliantDevices} compliant endpoints` : 'Admin/viewer only'}
          label="Total devices"
          tone="default"
          value={canViewSecurityData ? devices.length : 'Restricted'}
        />
        <MetricCard
          helper={canViewSecurityData ? `${highRiskAlerts} high or critical` : 'Admin/viewer only'}
          label="Open alerts"
          tone={highRiskAlerts > 0 ? 'danger' : 'success'}
          value={canViewSecurityData ? alerts.length : 'Restricted'}
        />
        <MetricCard
          helper={canViewSecurityData ? 'Latest metadata records' : 'Admin/viewer only'}
          label="Recent traffic"
          tone="default"
          value={canViewSecurityData ? traffic.length : 'Restricted'}
        />
        <MetricCard
          helper={isAdmin ? 'From latest audit log page' : 'Admin only'}
          label="Access failures"
          tone={accessFailures > 0 ? 'warning' : 'success'}
          value={isAdmin ? accessFailures : 'Restricted'}
        />
      </section>

      <section className="panel-grid dashboard-panels">
        <article className="panel">
          <h2>Session posture</h2>
          <dl>
            <div>
              <dt>Email</dt>
              <dd>{currentUser?.email ?? 'Unknown'}</dd>
            </div>
            <div>
              <dt>MFA</dt>
              <dd>{currentUser?.mfa_enabled ? 'Enabled' : 'Not enabled'}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{currentUser?.is_active ? 'Active' : 'Inactive'}</dd>
            </div>
            <div>
              <dt>Roles</dt>
              <dd>{currentUser?.roles.map((role) => role.name).join(', ') || 'None'}</dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <h2>Data health</h2>
          <ul className="feature-list">
            <li>Devices: {devicesQuery.isError ? getApiErrorMessage(devicesQuery.error) : 'ready'}</li>
            <li>
              Alerts: {openAlertsQuery.isError ? getApiErrorMessage(openAlertsQuery.error) : 'ready'}
            </li>
            <li>Traffic: {trafficQuery.isError ? getApiErrorMessage(trafficQuery.error) : 'ready'}</li>
            <li>Logs: {logsQuery.isError ? getApiErrorMessage(logsQuery.error) : isAdmin ? 'ready' : 'admin only'}</li>
          </ul>
        </article>
      </section>
    </main>
  )
}
