import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { MfaEnrollCard } from '@/components/auth/mfa-enroll-card'
import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { TableCard, tableClassName, tdClassName, thClassName } from '@/components/common/table'
import { useRole } from '@/hooks/use-role'
import { formatDateTime } from '@/lib/format'
import { getApiErrorMessage } from '@/services/api-client'
import { deviceService } from '@/services/device-service'
import { protectedService } from '@/services/protected-service'
import { useAuthStore } from '@/stores/auth-store'

const inputClassName =
  'ui-input'
const buttonClassName =
  'ui-button-primary'

function sensitivityTone(sensitivity: string): 'success' | 'warning' | 'danger' | 'info' {
  if (sensitivity === 'restricted') return 'danger'
  if (sensitivity === 'high') return 'warning'
  if (sensitivity === 'confidential') return 'info'
  return 'success'
}

export function ProtectedFilesPage() {
  const currentUser = useAuthStore((state) => state.currentUser)
  const { canViewSecurityData } = useRole()
  const [deviceId, setDeviceId] = useState('')

  const devicesQuery = useQuery({
    queryKey: ['protected-files', 'devices'],
    queryFn: () => deviceService.list({ limit: 100 }),
    enabled: canViewSecurityData,
  })

  const filesMutation = useMutation({
    mutationFn: () => protectedService.getFiles(Number(deviceId)),
  })

  const compliantDevices = devicesQuery.data?.devices.filter((device) => device.is_compliant) ?? []

  return (
    <PageShell
      description="Demonstrate the full Zero-Trust access chain: authentication, MFA, RBAC, and compliant device posture."
      eyebrow="Zero-Trust demo"
      title="Protected Files"
    >
      {!currentUser?.mfa_enabled && <MfaEnrollCard />}

      <section className="ui-panel">
        <h2 className="text-lg font-semibold text-zinc-950">Access request</h2>
        <p className="mt-2 text-zinc-600">
          Select or enter a compliant device ID. The backend receives it as the X-Device-ID header.
        </p>

        <div className="mt-5 grid grid-cols-[1fr_auto] gap-3 max-sm:grid-cols-1">
          {canViewSecurityData ? (
            <select className={inputClassName} onChange={(event) => setDeviceId(event.target.value)} value={deviceId}>
              <option value="">Select compliant device</option>
              {compliantDevices.map((device) => (
                <option key={device.id} value={device.id}>
                  #{device.id} {device.hostname} — last seen {formatDateTime(device.last_seen)}
                </option>
              ))}
            </select>
          ) : (
            <input
              className={inputClassName}
              min="1"
              onChange={(event) => setDeviceId(event.target.value)}
              placeholder="Compliant device ID"
              type="number"
              value={deviceId}
            />
          )}

          <button
            className={buttonClassName}
            disabled={filesMutation.isPending || !deviceId}
            onClick={() => filesMutation.mutate()}
            type="button"
          >
            {filesMutation.isPending ? 'Requesting...' : 'Request files'}
          </button>
        </div>

        {canViewSecurityData && devicesQuery.isLoading && <div className="mt-4"><LoadingState message="Loading compliant devices..." /></div>}
        {canViewSecurityData && devicesQuery.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(devicesQuery.error)} /></div>}
        {filesMutation.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(filesMutation.error)} /></div>}
      </section>

      {filesMutation.data && (
        <section className="grid gap-4">
          <div className="rounded-2xl border border-emerald-700/15 bg-emerald-50 p-5 text-emerald-800">
            <strong>{filesMutation.data.message}</strong>
            <p className="mt-1 text-emerald-800/80">
              User {filesMutation.data.user} accessed files from device {filesMutation.data.device}.
            </p>
          </div>

          <TableCard>
            <table className={tableClassName}>
              <thead>
                <tr>
                  <th className={thClassName}>File</th>
                  <th className={thClassName}>Size</th>
                  <th className={thClassName}>Sensitivity</th>
                </tr>
              </thead>
              <tbody>
                {filesMutation.data.files.map((file) => (
                  <tr key={file.name}>
                    <td className={tdClassName}>
                      <span className="font-semibold text-zinc-950">{file.name}</span>
                    </td>
                    <td className={tdClassName}>{file.size}</td>
                    <td className={tdClassName}>
                      <StatusBadge tone={sensitivityTone(file.sensitivity)}>{file.sensitivity}</StatusBadge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableCard>
        </section>
      )}
    </PageShell>
  )
}
