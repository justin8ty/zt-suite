import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { EmptyState } from '@/components/common/empty-state'
import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { TableCard, tableClassName, tdClassName, thClassName } from '@/components/common/table'
import { formatBytes, formatDateTime } from '@/lib/format'
import { getApiErrorMessage } from '@/services/api-client'
import { flowService } from '@/services/flow-service'

const inputClassName =
  'ui-input'

function packetTotal(flow: { total_fwd_packets: number | null; total_bwd_packets: number | null }) {
  return (flow.total_fwd_packets ?? 0) + (flow.total_bwd_packets ?? 0)
}

function byteTotal(flow: { total_fwd_bytes: number | null; total_bwd_bytes: number | null }) {
  return (flow.total_fwd_bytes ?? 0) + (flow.total_bwd_bytes ?? 0)
}

export function FlowsPage() {
  const [deviceId, setDeviceId] = useState('')
  const [prediction, setPrediction] = useState('')

  const flowsQuery = useQuery({
    queryKey: ['flows', deviceId, prediction],
    queryFn: () =>
      flowService.list({
        limit: 200,
        device_id: deviceId ? Number(deviceId) : undefined,
        prediction: prediction ? Number(prediction) : undefined,
      }),
    refetchInterval: 10_000,
  })

  const flows = flowsQuery.data ?? []
  const maliciousCount = flows.filter((flow) => flow.prediction === 1).length
  const totalBytes = flows.reduce((total, flow) => total + byteTotal(flow), 0)

  return (
    <PageShell
      actions={
        <div className="flex flex-wrap gap-2">
          <input
            className={inputClassName}
            min="1"
            onChange={(event) => setDeviceId(event.target.value)}
            placeholder="Filter device ID"
            type="number"
            value={deviceId}
          />
          <select className={inputClassName} onChange={(event) => setPrediction(event.target.value)} value={prediction}>
            <option value="">All predictions</option>
            <option value="1">Malicious only</option>
            <option value="0">Benign only</option>
          </select>
        </div>
      }
      description="Inspect CICFlowMeter-derived flow rows scored by endpoint IDS models."
      eyebrow="Flow IDS"
      title="Network Flows"
    >
      <section className="grid grid-cols-3 gap-3.5 max-md:grid-cols-1">
        <div className="ui-panel ui-card-hover">
          <span className="text-sm text-zinc-600">Flows loaded</span>
          <strong className="mt-2 block text-3xl text-zinc-950">{flows.length}</strong>
        </div>
        <div className="ui-panel ui-card-hover">
          <span className="text-sm text-zinc-600">Malicious predictions</span>
          <strong className="mt-2 block text-3xl text-zinc-950">{maliciousCount}</strong>
        </div>
        <div className="ui-panel ui-card-hover">
          <span className="text-sm text-zinc-600">Flow bytes</span>
          <strong className="mt-2 block text-3xl text-zinc-950">{formatBytes(totalBytes)}</strong>
        </div>
      </section>

      {flowsQuery.isLoading && <LoadingState message="Loading scored flows..." />}
      {flowsQuery.isError && <ErrorState message={getApiErrorMessage(flowsQuery.error)} />}

      {flowsQuery.data?.length === 0 && (
        <EmptyState title="No scored flows" message="No CICFlowMeter flow rows match the current filter." />
      )}

      {flowsQuery.data && flowsQuery.data.length > 0 && (
        <TableCard>
          <table className={tableClassName}>
            <thead>
              <tr>
                <th className={thClassName}>Timestamp</th>
                <th className={thClassName}>Device</th>
                <th className={thClassName}>Source</th>
                <th className={thClassName}>Destination</th>
                <th className={thClassName}>Protocol</th>
                <th className={thClassName}>Packets</th>
                <th className={thClassName}>Bytes</th>
                <th className={thClassName}>Score</th>
                <th className={thClassName}>Prediction</th>
              </tr>
            </thead>
            <tbody>
              {flowsQuery.data.map((flow) => (
                <tr key={flow.id}>
                  <td className={tdClassName}>{formatDateTime(flow.timestamp)}</td>
                  <td className={tdClassName}>{flow.device_id}</td>
                  <td className={tdClassName}>{flow.src_ip ?? '—'}:{flow.src_port ?? '—'}</td>
                  <td className={tdClassName}>{flow.dst_ip ?? '—'}:{flow.dst_port ?? '—'}</td>
                  <td className={tdClassName}>{flow.protocol ?? '—'}</td>
                  <td className={tdClassName}>{packetTotal(flow)}</td>
                  <td className={tdClassName}>{formatBytes(byteTotal(flow))}</td>
                  <td className={tdClassName}>{flow.malicious_score?.toFixed(3) ?? '—'}</td>
                  <td className={tdClassName}>
                    <StatusBadge tone={flow.prediction === 1 ? 'danger' : 'success'}>
                      {flow.prediction_label ?? flow.detection_source}
                    </StatusBadge>
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
