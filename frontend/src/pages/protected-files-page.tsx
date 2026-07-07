import { useMutation, useQuery } from '@tanstack/react-query'

import { MfaEnrollCard } from '@/components/auth/mfa-enroll-card'
import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { TableCard, tableClassName, tdClassName, thClassName } from '@/components/common/table'
import { getApiErrorMessage } from '@/services/api-client'
import { deviceService } from '@/services/device-service'
import { localAgentService } from '@/services/local-agent-service'
import { protectedService } from '@/services/protected-service'
import { useAuthStore } from '@/stores/auth-store'

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

  const localAgentQuery = useQuery({
    queryKey: ['local-agent', 'identity'],
    queryFn: localAgentService.getIdentity,
    retry: false,
    refetchInterval: 30_000,
  })

  const localDeviceId = localAgentQuery.data?.device_id ?? null

  const deviceQuery = useQuery({
    queryKey: ['protected-files', 'current-device', localDeviceId],
    queryFn: () => deviceService.getById(Number(localDeviceId)),
    enabled: localDeviceId !== null,
  })

  const filesMutation = useMutation({
    mutationFn: () => protectedService.getFiles(Number(localDeviceId)),
  })

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
          This page uses the local ZT Agent to detect the current device. The backend still verifies MFA, role, ownership, and device compliance before granting access.
        </p>

        <div className="mt-5 rounded-2xl border border-zinc-200 bg-zinc-50 p-4">
          <span className="text-sm font-medium text-zinc-700">Detected device</span>
          {localAgentQuery.isLoading && <div className="mt-3"><LoadingState message="Detecting local ZT Agent..." /></div>}
          {localAgentQuery.isError && (
            <div className="mt-3">
              <ErrorState message="ZT Agent was not detected on this device. Start the local agent and refresh this page." />
            </div>
          )}
          {localAgentQuery.data && localDeviceId === null && (
            <div className="mt-3">
              <ErrorState message="ZT Agent is running, but no backend device ID is configured." />
            </div>
          )}
          {deviceQuery.isLoading && <div className="mt-3"><LoadingState message="Loading current device posture..." /></div>}
          {deviceQuery.isError && <div className="mt-3"><ErrorState message={getApiErrorMessage(deviceQuery.error)} /></div>}
          {deviceQuery.data && (
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <div>
                <strong className="text-zinc-950">#{deviceQuery.data.id} {deviceQuery.data.hostname}</strong>
                <p className="mt-1 text-sm text-zinc-600">
                  {deviceQuery.data.os_type}{deviceQuery.data.os_version ? ` ${deviceQuery.data.os_version}` : ''}
                </p>
              </div>
              <StatusBadge tone={deviceQuery.data.is_compliant ? 'success' : 'danger'}>
                {deviceQuery.data.is_compliant ? 'Compliant' : 'Not compliant'}
              </StatusBadge>
            </div>
          )}
        </div>

        <div className="mt-5 flex justify-end">
          <button
            className={buttonClassName}
            disabled={filesMutation.isPending || localDeviceId === null || !deviceQuery.data?.is_compliant}
            onClick={() => filesMutation.mutate()}
            type="button"
          >
            {filesMutation.isPending ? 'Requesting...' : 'Request files'}
          </button>
        </div>

        {filesMutation.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(filesMutation.error)} /></div>}
      </section>

      {filesMutation.data && (
        <section className="grid gap-4">
          <div className="rounded-2xl border border-green-700/15 bg-green-50 p-5 text-green-800">
            <strong>{filesMutation.data.message}</strong>
            <p className="mt-1 text-green-800/80">
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
