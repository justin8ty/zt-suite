import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { TableCard, tableClassName, tdClassName, thClassName } from '@/components/common/table'
import { formatBytes, formatDateTime } from '@/lib/format'
import { getApiErrorMessage } from '@/services/api-client'
import { trafficService } from '@/services/traffic-service'

const inputClassName =
  'rounded-xl border border-slate-400/30 bg-slate-950/60 px-3 py-2.5 text-slate-50 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/15'

export function TrafficPage() {
  const [deviceId, setDeviceId] = useState('')

  const trafficQuery = useQuery({
    queryKey: ['traffic', deviceId],
    queryFn: () =>
      trafficService.list({
        limit: 200,
        device_id: deviceId ? Number(deviceId) : undefined,
      }),
    refetchInterval: 10_000,
  })

  const records = trafficQuery.data ?? []
  const totalBytes = records.reduce((total, record) => total + record.bytes_sent + record.bytes_received, 0)
  const uniqueDestinations = new Set(records.map((record) => record.dst_ip)).size
  const tcpCount = records.filter((record) => record.protocol.toUpperCase() === 'TCP').length

  return (
    <PageShell
      actions={
        <input
          className={inputClassName}
          min="1"
          onChange={(event) => setDeviceId(event.target.value)}
          placeholder="Filter device ID"
          type="number"
          value={deviceId}
        />
      }
      description="Inspect network traffic metadata uploaded by endpoint agents."
      eyebrow="Network visibility"
      title="Traffic"
    >
      <section className="grid grid-cols-3 gap-3.5 max-md:grid-cols-1">
        <div className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl">
          <span className="text-sm text-slate-400">Records loaded</span>
          <strong className="mt-2 block text-3xl text-slate-50">{records.length}</strong>
        </div>
        <div className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl">
          <span className="text-sm text-slate-400">Unique destinations</span>
          <strong className="mt-2 block text-3xl text-slate-50">{uniqueDestinations}</strong>
        </div>
        <div className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl">
          <span className="text-sm text-slate-400">Total bytes</span>
          <strong className="mt-2 block text-3xl text-slate-50">{formatBytes(totalBytes)}</strong>
          <p className="text-sm text-slate-400">TCP records: {tcpCount}</p>
        </div>
      </section>

      {trafficQuery.isLoading && <LoadingState message="Loading traffic..." />}
      {trafficQuery.isError && <ErrorState message={getApiErrorMessage(trafficQuery.error)} />}

      {trafficQuery.data && (
        <TableCard>
          <table className={tableClassName}>
            <thead>
              <tr>
                <th className={thClassName}>Timestamp</th>
                <th className={thClassName}>Device</th>
                <th className={thClassName}>Source</th>
                <th className={thClassName}>Destination</th>
                <th className={thClassName}>Protocol</th>
                <th className={thClassName}>Sent</th>
                <th className={thClassName}>Received</th>
              </tr>
            </thead>
            <tbody>
              {trafficQuery.data.map((record) => (
                <tr key={record.id}>
                  <td className={tdClassName}>{formatDateTime(record.timestamp)}</td>
                  <td className={tdClassName}>{record.device_id}</td>
                  <td className={tdClassName}>{record.src_ip}:{record.src_port}</td>
                  <td className={tdClassName}>{record.dst_ip}:{record.dst_port}</td>
                  <td className={tdClassName}>
                    <StatusBadge tone={record.protocol.toUpperCase() === 'TCP' ? 'info' : 'default'}>
                      {record.protocol}
                    </StatusBadge>
                  </td>
                  <td className={tdClassName}>{formatBytes(record.bytes_sent)}</td>
                  <td className={tdClassName}>{formatBytes(record.bytes_received)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
      )}
    </PageShell>
  )
}
