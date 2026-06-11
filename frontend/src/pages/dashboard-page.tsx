import { useQuery } from '@tanstack/react-query'

import { ErrorState } from '@/components/common/error-state'
import { MetricCard } from '@/components/dashboard/metric-card'
import { useRole } from '@/hooks/use-role'
import { formatBytes } from '@/lib/format'
import { getApiErrorMessage } from '@/services/api-client'
import { alertService } from '@/services/alert-service'
import { deviceService } from '@/services/device-service'
import { logService } from '@/services/log-service'
import { trafficService } from '@/services/traffic-service'
import { useAuthStore } from '@/stores/auth-store'

const DASHBOARD_REFETCH_MS = 10_000

const panelClassName =
  'ui-panel'
const detailRowClassName = 'flex justify-between gap-4 border-b border-zinc-950/10 pb-3 max-md:flex-col'
const chartCardClassName =
  'ui-panel ui-card-hover'

type SeverityKey = 'critical' | 'high' | 'medium' | 'low' | 'other'

const severityConfig: Record<SeverityKey, { label: string; className: string }> = {
  critical: { label: 'Critical', className: 'bg-red-400' },
  high: { label: 'High', className: 'bg-orange-300' },
  medium: { label: 'Medium', className: 'bg-yellow-300' },
  low: { label: 'Low', className: 'bg-sky-300' },
  other: { label: 'Other', className: 'bg-zinc-400' },
}

function normalizeSeverity(severity: string): SeverityKey {
  const normalized = severity.toLowerCase()
  if (normalized === 'critical' || normalized === 'high' || normalized === 'medium' || normalized === 'low') {
    return normalized
  }
  return 'other'
}

function AlertSeverityChart({ alerts }: { alerts: Array<{ severity: string }> }) {
  const counts = alerts.reduce<Record<SeverityKey, number>>(
    (current, alert) => {
      current[normalizeSeverity(alert.severity)] += 1
      return current
    },
    { critical: 0, high: 0, medium: 0, low: 0, other: 0 },
  )
  const maxCount = Math.max(...Object.values(counts), 1)

  return (
    <article className={chartCardClassName}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">Alert severity distribution</h2>
          <p className="mt-1 text-sm text-zinc-600">Open alerts grouped by severity.</p>
        </div>
        <span className="rounded-full border border-zinc-950/10 px-3 py-1 text-sm font-semibold text-zinc-700">
          {alerts.length} total
        </span>
      </div>
      <div className="mt-5 grid gap-3">
        {(Object.keys(severityConfig) as SeverityKey[]).map((severity) => {
          const count = counts[severity]
          const width = `${Math.max((count / maxCount) * 100, count > 0 ? 8 : 0)}%`

          return (
            <div className="grid grid-cols-[80px_1fr_32px] items-center gap-3" key={severity}>
              <span className="text-sm text-zinc-700">{severityConfig[severity].label}</span>
              <div className="h-3 overflow-hidden rounded-full bg-zinc-100">
                <div className={`h-full rounded-full ${severityConfig[severity].className}`} style={{ width }} />
              </div>
              <span className="text-right text-sm font-semibold text-zinc-950">{count}</span>
            </div>
          )
        })}
      </div>
    </article>
  )
}

function TrafficVolumeChart({
  records,
}: {
  records: Array<{ bytes_received: number; bytes_sent: number; timestamp: string }>
}) {
  const bucketMap = records.reduce<Map<string, number>>((current, record) => {
    const date = new Date(record.timestamp)
    if (Number.isNaN(date.getTime())) return current

    date.setSeconds(0, 0)
    const key = date.toISOString()
    current.set(key, (current.get(key) ?? 0) + record.bytes_sent + record.bytes_received)
    return current
  }, new Map())

  const buckets = Array.from(bucketMap.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .slice(-8)
    .map(([key, bytes]) => ({
      bytes,
      label: new Date(key).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }),
    }))
  const maxBytes = Math.max(...buckets.map((bucket) => bucket.bytes), 1)

  return (
    <article className={chartCardClassName}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">Traffic volume over time</h2>
          <p className="mt-1 text-sm text-zinc-600">Recent uploaded metadata grouped by minute.</p>
        </div>
        <span className="rounded-full border border-zinc-950/10 px-3 py-1 text-sm font-semibold text-zinc-700">
          {formatBytes(buckets.reduce((total, bucket) => total + bucket.bytes, 0))}
        </span>
      </div>
      {buckets.length === 0 ? (
        <p className="mt-6 text-sm text-zinc-600">No traffic records available yet.</p>
      ) : (
        <div className="mt-6 flex h-44 items-end gap-2 border-b border-zinc-950/10 pb-3">
          {buckets.map((bucket) => {
            const height = `${Math.max((bucket.bytes / maxBytes) * 100, 6)}%`

            return (
              <div className="flex min-w-0 flex-1 flex-col items-center gap-2" key={bucket.label}>
                <div className="flex h-32 w-full items-end rounded-t-2xl bg-zinc-50 p-1">
                  <div
                    aria-label={`${bucket.label}: ${formatBytes(bucket.bytes)}`}
                    className="w-full rounded-t-xl bg-emerald-600"
                    style={{ height }}
                    title={`${bucket.label}: ${formatBytes(bucket.bytes)}`}
                  />
                </div>
                <span className="font-mono text-[0.68rem] text-zinc-600">{bucket.label}</span>
              </div>
            )
          })}
        </div>
      )}
    </article>
  )
}

function ComplianceBreakdownChart({ devices }: { devices: Array<{ is_compliant: boolean }> }) {
  const compliant = devices.filter((device) => device.is_compliant).length
  const nonCompliant = devices.length - compliant
  const compliantPercentage = devices.length === 0 ? 0 : Math.round((compliant / devices.length) * 100)

  return (
    <article className={chartCardClassName}>
      <h2 className="text-lg font-semibold text-zinc-950">Device compliance breakdown</h2>
      <p className="mt-1 text-sm text-zinc-600">Current endpoint posture status.</p>
      <div className="mt-6 flex items-center gap-6 max-sm:flex-col">
        <div
          aria-label={`${compliantPercentage}% compliant devices`}
          className="grid size-36 shrink-0 place-items-center rounded-full"
          style={{
            background: `conic-gradient(rgb(74 222 128) 0 ${compliantPercentage}%, rgb(248 113 113) ${compliantPercentage}% 100%)`,
          }}
        >
          <div className="grid size-24 place-items-center rounded-full bg-white text-center shadow-inner shadow-zinc-950/10">
            <strong className="text-2xl text-zinc-950">{compliantPercentage}%</strong>
            <span className="text-xs text-zinc-600">compliant</span>
          </div>
        </div>
        <div className="grid flex-1 gap-3 text-sm">
          <div className="flex items-center justify-between gap-3 rounded-2xl bg-zinc-50 px-4 py-3">
            <span className="flex items-center gap-2 text-zinc-700">
              <span className="size-2.5 rounded-full bg-green-400" /> Compliant
            </span>
            <strong className="text-zinc-950">{compliant}</strong>
          </div>
          <div className="flex items-center justify-between gap-3 rounded-2xl bg-zinc-50 px-4 py-3">
            <span className="flex items-center gap-2 text-zinc-700">
              <span className="size-2.5 rounded-full bg-red-400" /> Non-compliant
            </span>
            <strong className="text-zinc-950">{nonCompliant}</strong>
          </div>
          <div className="flex items-center justify-between gap-3 rounded-2xl bg-zinc-50 px-4 py-3">
            <span className="text-zinc-700">Registered devices</span>
            <strong className="text-zinc-950">{devices.length}</strong>
          </div>
        </div>
      </div>
    </article>
  )
}

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
    <main className="grid gap-5" id="main-content">
      <div className="px-1 py-2">
        <div className="ui-eyebrow mb-3">
          Live overview
        </div>
        <h1 className="ui-title">
          Security dashboard
        </h1>
        <p className="mt-3.5 max-w-3xl text-zinc-600">
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

      {canViewSecurityData && (
        <section className="grid grid-cols-3 gap-5 max-2xl:grid-cols-2 max-lg:grid-cols-1" aria-label="Security visualizations">
          <AlertSeverityChart alerts={alerts} />
          <TrafficVolumeChart records={traffic} />
          <ComplianceBreakdownChart devices={devices} />
        </section>
      )}

      <section className="grid grid-cols-2 gap-5 max-lg:grid-cols-1">
        <article className={panelClassName}>
          <h2 className="text-lg font-semibold text-zinc-950">Session posture</h2>
          <dl className="mt-5 grid gap-3.5">
            <div className={detailRowClassName}>
              <dt className="text-zinc-600">Email</dt>
              <dd className="m-0 text-right font-semibold text-zinc-950 max-md:text-left">
                {currentUser?.email ?? 'Unknown'}
              </dd>
            </div>
            <div className={detailRowClassName}>
              <dt className="text-zinc-600">MFA</dt>
              <dd className="m-0 text-right font-semibold text-zinc-950 max-md:text-left">
                {currentUser?.mfa_enabled ? 'Enabled' : 'Not enabled'}
              </dd>
            </div>
            <div className={detailRowClassName}>
              <dt className="text-zinc-600">Status</dt>
              <dd className="m-0 text-right font-semibold text-zinc-950 max-md:text-left">
                {currentUser?.is_active ? 'Active' : 'Inactive'}
              </dd>
            </div>
            <div className={detailRowClassName}>
              <dt className="text-zinc-600">Roles</dt>
              <dd className="m-0 text-right font-semibold text-zinc-950 max-md:text-left">
                {currentUser?.roles.map((role) => role.name).join(', ') || 'None'}
              </dd>
            </div>
          </dl>
        </article>

        <article className={panelClassName}>
          <h2 className="text-lg font-semibold text-zinc-950">Data health</h2>
          <ul className="mt-5 grid gap-3 pl-5 text-zinc-700">
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
