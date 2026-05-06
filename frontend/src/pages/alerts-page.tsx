import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { EmptyState } from '@/components/common/empty-state'
import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { TableCard, tableClassName, tdClassName, thClassName } from '@/components/common/table'
import { formatDateTime } from '@/lib/format'
import { getApiErrorMessage } from '@/services/api-client'
import { alertService } from '@/services/alert-service'
import { useRole } from '@/hooks/use-role'

const inputClassName =
  'rounded-xl border border-slate-400/30 bg-slate-950/60 px-3 py-2.5 text-slate-50 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/15'
const buttonClassName =
  'min-h-10 rounded-xl bg-gradient-to-br from-sky-400 to-green-400 px-4 font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60'

function severityTone(severity: string): 'success' | 'warning' | 'danger' | 'info' {
  if (severity === 'critical' || severity === 'high') return 'danger'
  if (severity === 'medium') return 'warning'
  if (severity === 'low') return 'info'
  return 'success'
}

export function AlertsPage() {
  const queryClient = useQueryClient()
  const { isAdmin } = useRole()
  const [severity, setSeverity] = useState('')
  const [acknowledged, setAcknowledged] = useState('')

  const alertsQuery = useQuery({
    queryKey: ['alerts', severity, acknowledged],
    queryFn: () =>
      alertService.list({
        limit: 100,
        severity: severity || undefined,
        is_acknowledged: acknowledged === '' ? undefined : acknowledged === 'true',
      }),
    refetchInterval: 10_000,
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: number) => alertService.acknowledge(alertId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  return (
    <PageShell
      actions={
        <div className="flex gap-3 max-sm:w-full max-sm:flex-col">
          <select className={inputClassName} onChange={(event) => setSeverity(event.target.value)} value={severity}>
            <option value="">All severities</option>
            <option value="critical">critical</option>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
          </select>
          <select className={inputClassName} onChange={(event) => setAcknowledged(event.target.value)} value={acknowledged}>
            <option value="">All statuses</option>
            <option value="false">Open</option>
            <option value="true">Acknowledged</option>
          </select>
        </div>
      }
      description="Triage reported anomalies and acknowledge security alerts."
      eyebrow="Monitoring"
      title="Alerts"
    >
      {acknowledgeMutation.isError && <ErrorState message={getApiErrorMessage(acknowledgeMutation.error)} />}
      {alertsQuery.isLoading && <LoadingState message="Loading alerts..." />}
      {alertsQuery.isError && <ErrorState message={getApiErrorMessage(alertsQuery.error)} />}

      {alertsQuery.data?.length === 0 && (
        <EmptyState title="No alerts found" message="No alerts match the current filters." />
      )}

      {alertsQuery.data && alertsQuery.data.length > 0 && (
        <TableCard>
          <table className={tableClassName}>
            <thead>
              <tr>
                <th className={thClassName}>Alert</th>
                <th className={thClassName}>Severity</th>
                <th className={thClassName}>Category</th>
                <th className={thClassName}>Device</th>
                <th className={thClassName}>Source</th>
                <th className={thClassName}>Status</th>
                <th className={thClassName}>Timestamp</th>
                <th className={thClassName}>Action</th>
              </tr>
            </thead>
            <tbody>
              {alertsQuery.data.map((alert) => (
                <tr key={alert.id}>
                  <td className={tdClassName}>
                    <div className="font-bold text-slate-50">{alert.title}</div>
                    <div className="max-w-md text-xs text-slate-400">{alert.description}</div>
                  </td>
                  <td className={tdClassName}>
                    <StatusBadge tone={severityTone(alert.severity.toLowerCase())}>{alert.severity}</StatusBadge>
                  </td>
                  <td className={tdClassName}>{alert.category}</td>
                  <td className={tdClassName}>{alert.device_id}</td>
                  <td className={tdClassName}>{alert.source_ip ?? '—'}</td>
                  <td className={tdClassName}>
                    <StatusBadge tone={alert.is_acknowledged ? 'success' : 'warning'}>
                      {alert.is_acknowledged ? 'Acknowledged' : 'Open'}
                    </StatusBadge>
                  </td>
                  <td className={tdClassName}>{formatDateTime(alert.timestamp)}</td>
                  <td className={tdClassName}>
                    {isAdmin && !alert.is_acknowledged ? (
                      <button
                        className={buttonClassName}
                        disabled={acknowledgeMutation.isPending}
                        onClick={() => acknowledgeMutation.mutate(alert.id)}
                        type="button"
                      >
                        Acknowledge
                      </button>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
      )}
    </PageShell>
  )
}
