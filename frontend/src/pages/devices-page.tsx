import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/empty-state'
import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { TableCard, tableClassName, tdClassName, thClassName } from '@/components/common/table'
import { formatDateTime } from '@/lib/format'
import { routes } from '@/lib/routes'
import { getApiErrorMessage } from '@/services/api-client'
import { deviceService } from '@/services/device-service'

const inputClassName =
  'ui-input'
const buttonClassName =
  'ui-button-primary'

export function DevicesPage() {
  const queryClient = useQueryClient()
  const [hostname, setHostname] = useState('')
  const [osType, setOsType] = useState('windows')
  const [osVersion, setOsVersion] = useState('')
  const [agentVersion, setAgentVersion] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const devicesQuery = useQuery({
    queryKey: ['devices'],
    queryFn: () => deviceService.list({ limit: 100 }),
    refetchInterval: 10_000,
  })

  const registerMutation = useMutation({
    mutationFn: deviceService.register,
    onSuccess: async () => {
      setHostname('')
      setOsVersion('')
      setAgentVersion('')
      await queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    if (!hostname.trim()) {
      setFormError('Hostname is required.')
      return
    }

    await registerMutation.mutateAsync({
      hostname: hostname.trim(),
      os_type: osType,
      os_version: osVersion || null,
      agent_version: agentVersion || null,
    })
  }

  return (
    <PageShell
      description="Review registered endpoints, compliance status, owners, and latest heartbeat."
      eyebrow="Endpoint posture"
      title="Devices"
    >
      <form
        className="grid grid-cols-[1fr_160px_1fr_1fr_auto] gap-3 ui-panel ui-card-hover max-xl:grid-cols-1"
        onSubmit={handleRegister}
      >
        <input className={inputClassName} onChange={(event) => setHostname(event.target.value)} placeholder="hostname" required value={hostname} />
        <select className={inputClassName} onChange={(event) => setOsType(event.target.value)} value={osType}>
          <option value="windows">windows</option>
          <option value="linux">linux</option>
          <option value="macos">macos</option>
        </select>
        <input className={inputClassName} onChange={(event) => setOsVersion(event.target.value)} placeholder="OS version" value={osVersion} />
        <input className={inputClassName} onChange={(event) => setAgentVersion(event.target.value)} placeholder="Agent version" value={agentVersion} />
        <button className={buttonClassName} disabled={registerMutation.isPending} type="submit">
          {registerMutation.isPending ? 'Registering...' : 'Register'}
        </button>
      </form>

      {formError && <ErrorState title="Invalid device details" message={formError} />}
      {registerMutation.isError && <ErrorState message={getApiErrorMessage(registerMutation.error)} />}
      {devicesQuery.isLoading && <LoadingState message="Loading devices..." />}
      {devicesQuery.isError && <ErrorState message={getApiErrorMessage(devicesQuery.error)} />}

      {devicesQuery.data?.devices.length === 0 && (
        <EmptyState title="No devices registered" message="Register a device above or start an endpoint agent." />
      )}

      {devicesQuery.data && devicesQuery.data.devices.length > 0 && (
        <TableCard>
          <table className={tableClassName}>
            <thead>
              <tr>
                <th className={thClassName}>Hostname</th>
                <th className={thClassName}>OS</th>
                <th className={thClassName}>Agent</th>
                <th className={thClassName}>Compliance</th>
                <th className={thClassName}>Owner</th>
                <th className={thClassName}>Last seen</th>
                <th className={thClassName}>Details</th>
              </tr>
            </thead>
            <tbody>
              {devicesQuery.data.devices.map((device) => (
                <tr key={device.id}>
                  <td className={tdClassName}>
                    <div className="font-semibold text-zinc-950">{device.hostname}</div>
                    <div className="text-xs text-zinc-600">ID {device.id}</div>
                  </td>
                  <td className={tdClassName}>{device.os_type} {device.os_version ?? ''}</td>
                  <td className={tdClassName}>{device.agent_version ?? '—'}</td>
                  <td className={tdClassName}>
                    <StatusBadge tone={device.is_compliant ? 'success' : 'danger'}>
                      {device.is_compliant ? 'Compliant' : 'Non-compliant'}
                    </StatusBadge>
                  </td>
                  <td className={tdClassName}>{device.user_id ?? '—'}</td>
                  <td className={tdClassName}>{formatDateTime(device.last_seen)}</td>
                  <td className={tdClassName}>
                    <Link className="ui-link" to={`${routes.devices}/${device.id}`}>
                      Open
                    </Link>
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
