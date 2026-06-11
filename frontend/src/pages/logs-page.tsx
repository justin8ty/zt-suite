import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { EmptyState } from '@/components/common/empty-state'
import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { TableCard, tableClassName, tdClassName, thClassName } from '@/components/common/table'
import { formatDateTime } from '@/lib/format'
import { getApiErrorMessage } from '@/services/api-client'
import { logService } from '@/services/log-service'

const inputClassName =
  'ui-input'

export function LogsPage() {
  const [userId, setUserId] = useState('')
  const [action, setAction] = useState('')

  const logsQuery = useQuery({
    queryKey: ['logs', userId, action],
    queryFn: () =>
      logService.list({
        limit: 200,
        user_id: userId ? Number(userId) : undefined,
        action: action || undefined,
      }),
    refetchInterval: 10_000,
  })

  return (
    <PageShell
      actions={
        <div className="flex gap-3 max-sm:w-full max-sm:flex-col">
          <input className={inputClassName} onChange={(event) => setUserId(event.target.value)} placeholder="User ID" type="number" value={userId} />
          <input className={inputClassName} onChange={(event) => setAction(event.target.value)} placeholder="Action filter" value={action} />
        </div>
      }
      description="Audit authentication, authorization, and protected resource access events."
      eyebrow="Audit"
      title="Access Logs"
    >
      {logsQuery.isLoading && <LoadingState message="Loading logs..." />}
      {logsQuery.isError && <ErrorState message={getApiErrorMessage(logsQuery.error)} />}

      {logsQuery.data?.logs.length === 0 && (
        <EmptyState title="No access logs found" message="No audit events match the current filters." />
      )}

      {logsQuery.data && logsQuery.data.logs.length > 0 && (
        <TableCard>
          <table className={tableClassName}>
            <thead>
              <tr>
                <th className={thClassName}>Timestamp</th>
                <th className={thClassName}>User</th>
                <th className={thClassName}>Action</th>
                <th className={thClassName}>Status</th>
                <th className={thClassName}>Resource</th>
                <th className={thClassName}>Details</th>
              </tr>
            </thead>
            <tbody>
              {logsQuery.data.logs.map((log) => (
                <tr key={log.id}>
                  <td className={tdClassName}>{formatDateTime(log.timestamp)}</td>
                  <td className={tdClassName}>{log.user_id ?? '—'}</td>
                  <td className={tdClassName}>{log.action}</td>
                  <td className={tdClassName}>
                    <StatusBadge tone={log.status === 'success' ? 'success' : 'danger'}>{log.status}</StatusBadge>
                  </td>
                  <td className={tdClassName}>{log.resource ?? '—'}</td>
                  <td className={`${tdClassName} max-w-md text-xs text-zinc-600`}>{log.details ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
      )}
    </PageShell>
  )
}
