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
import type { PostureReportCreate } from '@/types/posture'

const checkboxClassName = 'size-4 accent-sky-400'
const buttonClassName =
  'min-h-10 rounded-xl bg-gradient-to-br from-sky-400 to-green-400 px-4 font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60'

export function DeviceDetailPage() {
  const queryClient = useQueryClient()
  const params = useParams()
  const deviceId = Number(params.deviceId)
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
