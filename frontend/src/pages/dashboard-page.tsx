import { useQuery } from '@tanstack/react-query'

import { ErrorState } from '@/components/common/error-state'
import { MetricCard } from '@/components/dashboard/metric-card'
import { useRole } from '@/hooks/use-role'
import { getApiErrorMessage } from '@/services/api-client'
import { alertService } from '@/services/alert-service'
import { deviceService } from '@/services/device-service'
import { logService } from '@/services/log-service'
import { trafficService } from '@/services/traffic-service'
import { useAuthStore } from '@/stores/auth-store'

const DASHBOARD_REFETCH_MS = 10_000

const panelClassName =
  'rounded-3xl border border-slate-400/20 bg-slate-900/80 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl'
const detailRowClassName = 'flex justify-between gap-4 border-b border-slate-400/15 pb-3 max-md:flex-col'

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
    <main className="grid gap-5">
      <div className="px-1 py-2">
        <div className="mb-3.5 text-xs font-extrabold tracking-[0.18em] text-cyan-300 uppercase">
          Live overview
        </div>
        <h1 className="text-4xl leading-none font-bold tracking-tight text-slate-50 md:text-6xl">
          Security dashboard
        </h1>
        <p className="mt-3.5 max-w-3xl text-slate-400">
          Welcome{currentUser ? `, ${currentUser.email}` : ''}. Dashboard data refreshes every 10
          seconds where your role permits access.
        </p>
      </div>

      {!canViewSecurityData && (
        <ErrorState
          title="Limited dashboard access"
          message="Your role can access protected app features, but security metrics require admin or viewer role."
        />
      )}

      <section className="grid grid-cols-4 gap-3.5 max-xl:grid-cols-2 max-sm:grid-cols-1" aria-label="Security metrics">
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

      <section className="grid grid-cols-2 gap-5 max-lg:grid-cols-1">
        <article className={panelClassName}>
          <h2 className="text-lg font-bold text-slate-50">Session posture</h2>
          <dl className="mt-5 grid gap-3.5">
            <div className={detailRowClassName}>
              <dt className="text-slate-400">Email</dt>
              <dd className="m-0 text-right font-bold text-slate-50 max-md:text-left">
                {currentUser?.email ?? 'Unknown'}
              </dd>
            </div>
            <div className={detailRowClassName}>
              <dt className="text-slate-400">MFA</dt>
              <dd className="m-0 text-right font-bold text-slate-50 max-md:text-left">
                {currentUser?.mfa_enabled ? 'Enabled' : 'Not enabled'}
              </dd>
            </div>
            <div className={detailRowClassName}>
              <dt className="text-slate-400">Status</dt>
              <dd className="m-0 text-right font-bold text-slate-50 max-md:text-left">
                {currentUser?.is_active ? 'Active' : 'Inactive'}
              </dd>
            </div>
            <div className={detailRowClassName}>
              <dt className="text-slate-400">Roles</dt>
              <dd className="m-0 text-right font-bold text-slate-50 max-md:text-left">
                {currentUser?.roles.map((role) => role.name).join(', ') || 'None'}
              </dd>
            </div>
          </dl>
        </article>

        <article className={panelClassName}>
          <h2 className="text-lg font-bold text-slate-50">Data health</h2>
          <ul className="mt-5 grid gap-3 pl-5 text-slate-300">
            <li>Devices: {devicesQuery.isError ? getApiErrorMessage(devicesQuery.error) : 'ready'}</li>
            <li>
              Alerts: {openAlertsQuery.isError ? getApiErrorMessage(openAlertsQuery.error) : 'ready'}
            </li>
            <li>Traffic: {trafficQuery.isError ? getApiErrorMessage(trafficQuery.error) : 'ready'}</li>
            <li>
              Logs: {logsQuery.isError ? getApiErrorMessage(logsQuery.error) : isAdmin ? 'ready' : 'admin only'}
            </li>
          </ul>
        </article>
      </section>
    </main>
  )
}
