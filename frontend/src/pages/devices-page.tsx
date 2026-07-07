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
import { useRole } from '@/hooks/use-role'
import { getApiErrorMessage } from '@/services/api-client'
import { deviceService } from '@/services/device-service'
import { userService } from '@/services/user-service'
import type { AgentTokenIssued, Device } from '@/types/device'

const inputClassName =
  'ui-input'
const buttonClassName =
  'ui-button-primary'

export function DevicesPage() {
  const queryClient = useQueryClient()
  const { isAdmin } = useRole()
  const [hostname, setHostname] = useState('')
  const [ownerId, setOwnerId] = useState('')
  const [tokenName, setTokenName] = useState('default agent')
  const [enrolledDevice, setEnrolledDevice] = useState<Device | null>(null)
  const [issuedToken, setIssuedToken] = useState<AgentTokenIssued | null>(null)
  const [copied, setCopied] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const devicesQuery = useQuery({
    queryKey: ['devices'],
    queryFn: () => deviceService.list({ limit: 100 }),
    refetchInterval: 10_000,
  })

  const usersQuery = useQuery({
    queryKey: ['users', 'device-owners'],
    queryFn: () => userService.list({ limit: 100 }),
    enabled: isAdmin,
  })

  const registerMutation = useMutation({
    mutationFn: deviceService.register,
    onSuccess: async (device) => {
      setHostname('')
      setEnrolledDevice(device)
      setIssuedToken(null)
      await queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })

  const issueTokenMutation = useMutation({
    mutationFn: () => {
      if (!enrolledDevice) throw new Error('Register a device before issuing a token')
      return deviceService.issueAgentToken(enrolledDevice.id, { name: tokenName || 'default agent' })
    },
    onSuccess: (token) => {
      setIssuedToken(token)
      setTokenName('default agent')
    },
  })

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    if (!hostname.trim()) {
      setFormError('Hostname is required.')
      return
    }

    if (isAdmin && !ownerId) {
      setFormError('Assign an owner for this device.')
      return
    }

    await registerMutation.mutateAsync({
      hostname: hostname.trim(),
      user_id: ownerId ? Number(ownerId) : undefined,
    })
  }

  return (
    <PageShell
      description="Review registered endpoints, compliance status, owners, and latest heartbeat."
      eyebrow="Endpoint posture"
      title="Devices"
    >
      {isAdmin && (
        <section className="grid gap-4 ui-panel ui-card-hover">
          <div>
            <h2 className="text-lg font-semibold text-zinc-950">Enroll a device</h2>
            <p className="mt-1 text-sm text-zinc-600">
              Enter a hostname/label and assign an owner. OS and agent details will be filled by the endpoint agent after it runs.
            </p>
          </div>

          <form className="grid grid-cols-[1fr_1fr_auto] gap-3 max-xl:grid-cols-1" onSubmit={handleRegister}>
            <input className={inputClassName} onChange={(event) => setHostname(event.target.value)} placeholder="hostname or device label" required value={hostname} />
            <select className={inputClassName} onChange={(event) => setOwnerId(event.target.value)} required value={ownerId}>
              <option value="">Assign owner</option>
              {usersQuery.data?.users.map((user) => (
                <option key={user.id} value={user.id}>{user.email}</option>
              ))}
            </select>
            <button className={buttonClassName} disabled={registerMutation.isPending} type="submit">
              {registerMutation.isPending ? 'Creating...' : 'Create enrollment'}
            </button>
          </form>

          {usersQuery.isLoading && <LoadingState message="Loading users..." />}
          {usersQuery.isError && <ErrorState message={getApiErrorMessage(usersQuery.error)} />}

          {enrolledDevice && (
            <div className="rounded-2xl border border-amber-700/15 bg-amber-50 p-4">
              <h3 className="font-semibold text-amber-900">Next: issue an agent token</h3>
              <p className="mt-1 text-sm text-amber-800/80">
                Give the user device ID <strong>{enrolledDevice.id}</strong> and the one-time token. The agent will fill endpoint metadata after the first posture report.
              </p>
              <div className="mt-4 flex flex-wrap items-end gap-3">
                <div className="min-w-[220px] flex-1">
                  <label className="mb-1 block text-xs text-amber-900" htmlFor="enrollment-token-name">Token name</label>
                  <input
                    className="w-full ui-input"
                    id="enrollment-token-name"
                    onChange={(event) => setTokenName(event.target.value)}
                    value={tokenName}
                  />
                </div>
                <button className={buttonClassName} disabled={issueTokenMutation.isPending} onClick={() => issueTokenMutation.mutate()} type="button">
                  {issueTokenMutation.isPending ? 'Issuing...' : 'Issue token'}
                </button>
              </div>
              {issueTokenMutation.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(issueTokenMutation.error)} /></div>}
              {issuedToken && (
                <div className="mt-4 rounded-xl bg-white p-3">
                  <p className="text-sm font-semibold text-zinc-950">Copy this now. It will not be shown again.</p>
                  <div className="mt-2 flex items-center gap-2">
                    <code className="flex-1 overflow-x-auto rounded-lg bg-zinc-950 px-3 py-2 text-sm text-white">{issuedToken.token}</code>
                    <button
                      className="ui-button-secondary"
                      onClick={() => { navigator.clipboard.writeText(issuedToken.token); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
                      type="button"
                    >
                      Copy
                    </button>
                  </div>
                  <p className="mt-2 text-sm text-zinc-700">Configure the agent with:</p>
                  <pre className="mt-2 overflow-x-auto rounded-lg bg-zinc-950 p-3 text-sm text-white">{`ZT_AGENT_DEVICE_ID=${enrolledDevice.id}\nZT_AGENT_AGENT_TOKEN=${issuedToken.token}`}</pre>
                  {copied && <p className="mt-1 text-xs text-green-700">Copied</p>}
                </div>
              )}
            </div>
          )}
        </section>
      )}

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
