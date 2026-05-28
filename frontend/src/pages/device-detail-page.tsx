import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { formatDateTime } from '@/lib/format'
import { routes } from '@/lib/routes'
import { getApiErrorMessage } from '@/services/api-client'
import { deviceService } from '@/services/device-service'
import type { AgentTokenIssued } from '@/types/device'
import type { PostureReportCreate } from '@/types/posture'

const checkboxClassName = 'size-4 accent-sky-400'
const buttonClassName =
  'min-h-10 rounded-xl bg-gradient-to-br from-sky-400 to-green-400 px-4 font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60'

export function DeviceDetailPage() {
  const queryClient = useQueryClient()
  const params = useParams()
  const deviceId = Number(params.deviceId)
  const [tokenName, setTokenName] = useState('default agent')
  const [issuedToken, setIssuedToken] = useState<AgentTokenIssued | null>(null)
  const [copied, setCopied] = useState(false)
  const [posture, setPosture] = useState<PostureReportCreate>({
    antivirus_present: true,
    antivirus_enabled: true,
    firewall_enabled: true,
    disk_encrypted: false,
    os_up_to_date: true,
  })

  const deviceQuery = useQuery({
    queryKey: ['devices', deviceId],
    queryFn: () => deviceService.getById(deviceId),
    enabled: Number.isFinite(deviceId),
  })

  const postureQuery = useQuery({
    queryKey: ['devices', deviceId, 'posture'],
    queryFn: () => deviceService.getLatestPosture(deviceId),
    enabled: Number.isFinite(deviceId),
    retry: false,
  })

  const issueTokenMutation = useMutation({
    mutationFn: () => deviceService.issueAgentToken(deviceId, { name: tokenName || 'default agent' }),
    onSuccess: (data) => {
      setIssuedToken(data)
      setTokenName('default agent')
    },
  })

  const submitPostureMutation = useMutation({
    mutationFn: () => deviceService.submitPosture(deviceId, posture),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['devices'] }),
        queryClient.invalidateQueries({ queryKey: ['devices', deviceId] }),
        queryClient.invalidateQueries({ queryKey: ['devices', deviceId, 'posture'] }),
      ])
    },
  })

  function setPostureField(field: keyof PostureReportCreate, value: boolean) {
    setPosture((current) => ({ ...current, [field]: value }))
  }

  return (
    <PageShell
      actions={<Link className="font-bold text-cyan-300 hover:text-cyan-200" to={routes.devices}>Back to devices</Link>}
      description="Inspect endpoint metadata and latest posture evaluation."
      eyebrow="Device detail"
      title={deviceQuery.data?.hostname ?? 'Device'}
    >
      {deviceQuery.isLoading && <LoadingState message="Loading device..." />}
      {deviceQuery.isError && <ErrorState message={getApiErrorMessage(deviceQuery.error)} />}

      {deviceQuery.data && (
        <section className="grid grid-cols-2 gap-5 max-lg:grid-cols-1">
          <article className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
            <h2 className="text-lg font-bold text-slate-50">Device profile</h2>
            <dl className="mt-5 grid gap-3.5 text-slate-200">
              <div className="flex justify-between border-b border-slate-400/15 pb-3"><dt className="text-slate-400">OS</dt><dd>{deviceQuery.data.os_type} {deviceQuery.data.os_version ?? ''}</dd></div>
              <div className="flex justify-between border-b border-slate-400/15 pb-3"><dt className="text-slate-400">Agent</dt><dd>{deviceQuery.data.agent_version ?? '—'}</dd></div>
              <div className="flex justify-between border-b border-slate-400/15 pb-3"><dt className="text-slate-400">Owner</dt><dd>{deviceQuery.data.user_id ?? '—'}</dd></div>
              <div className="flex justify-between border-b border-slate-400/15 pb-3"><dt className="text-slate-400">Last seen</dt><dd>{formatDateTime(deviceQuery.data.last_seen)}</dd></div>
              <div className="flex justify-between border-b border-slate-400/15 pb-3"><dt className="text-slate-400">Compliance</dt><dd><StatusBadge tone={deviceQuery.data.is_compliant ? 'success' : 'danger'}>{deviceQuery.data.is_compliant ? 'Compliant' : 'Non-compliant'}</StatusBadge></dd></div>
            </dl>
          </article>

          <article className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
            <h2 className="text-lg font-bold text-slate-50">Latest posture</h2>
            {postureQuery.isLoading && <p className="mt-5 text-slate-400">Loading posture...</p>}
            {postureQuery.isError && <p className="mt-5 text-slate-400">No posture report found yet.</p>}
            {postureQuery.data && (
              <div className="mt-5 grid gap-3 text-slate-200">
                <div>Score: <strong className="text-slate-50">{postureQuery.data.compliance_score}/100</strong></div>
                <div>Antivirus: {postureQuery.data.antivirus_present && postureQuery.data.antivirus_enabled ? 'OK' : 'Fail'}</div>
                <div>Firewall: {postureQuery.data.firewall_enabled ? 'OK' : 'Fail'}</div>
                <div>Disk encryption: {postureQuery.data.disk_encrypted ? 'OK' : 'Fail'}</div>
                <div>OS updated: {postureQuery.data.os_up_to_date ? 'OK' : 'Fail'}</div>
                <div>Reported: {formatDateTime(postureQuery.data.timestamp)}</div>
              </div>
            )}
          </article>
        </section>
      )}

      <section className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
        <h2 className="flex items-center gap-2 text-lg font-bold text-slate-50">
          <svg className="size-5 text-amber-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg> Agent tokens
        </h2>
        <div className="mt-5 flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <label className="mb-1 block text-xs text-slate-400" htmlFor="token-name">Token name</label>
            <input
              className="w-full rounded-xl border border-slate-400/30 bg-slate-950/60 px-3 py-2.5 text-slate-50 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/15"
              id="token-name"
              onChange={(event) => setTokenName(event.target.value)}
              placeholder="e.g. workstation-alpha"
              value={tokenName}
            />
          </div>
          <button
            className={`${buttonClassName} flex items-center gap-2`}
            disabled={issueTokenMutation.isPending}
            onClick={() => issueTokenMutation.mutate()}
            type="button"
          >
            {issueTokenMutation.isPending ? 'Issuing...' : 'Issue token'}
          </button>
        </div>

        {issueTokenMutation.isError && (
          <div className="mt-4"><ErrorState message={getApiErrorMessage(issueTokenMutation.error)} /></div>
        )}

        {issuedToken && (
          <div className="mt-5 rounded-2xl border border-amber-400/30 bg-amber-950/30 p-4">
            <p className="mb-2 text-sm font-bold text-amber-300">Token issued — copy it now, it won&apos;t be shown again</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 overflow-x-auto rounded-xl bg-slate-950/80 px-3 py-2 text-sm text-slate-50">{issuedToken.token}</code>
              <button
                className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-slate-50"
                onClick={() => { navigator.clipboard.writeText(issuedToken.token); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
                title="Copy token"
                type="button"
              >
                <svg className="size-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect height="13" rx="2" ry="2" width="13" x="9" y="9"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              </button>
            </div>
            {copied && <p className="mt-1 text-xs text-green-400">Copied!</p>}
          </div>
        )}
      </section>

      <section className="rounded-3xl border border-slate-400/20 bg-slate-900/80 p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
        <h2 className="text-lg font-bold text-slate-50">Submit simulated posture</h2>
        <div className="mt-5 grid grid-cols-5 gap-3 text-sm text-slate-200 max-xl:grid-cols-2 max-sm:grid-cols-1">
          {Object.entries(posture).map(([key, value]) => (
            <label className="flex items-center gap-2" key={key}>
              <input className={checkboxClassName} checked={value} onChange={(event) => setPostureField(key as keyof PostureReportCreate, event.target.checked)} type="checkbox" />
              {key.replaceAll('_', ' ')}
            </label>
          ))}
        </div>
        <button className={`${buttonClassName} mt-5`} disabled={submitPostureMutation.isPending} onClick={() => submitPostureMutation.mutate()} type="button">
          {submitPostureMutation.isPending ? 'Submitting...' : 'Submit posture'}
        </button>
        {submitPostureMutation.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(submitPostureMutation.error)} /></div>}
      </section>
    </PageShell>
  )
}
