import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'

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
import type { ProtectedFile } from '@/types/protected-resource'

const buttonClassName =
  'ui-button-primary'

function sensitivityTone(sensitivity: string): 'success' | 'warning' | 'danger' | 'info' {
  if (sensitivity === 'restricted') return 'danger'
  if (sensitivity === 'high') return 'warning'
  if (sensitivity === 'confidential') return 'info'
  return 'success'
}

function parseCsv(content: string): string[][] {
  return content
    .trim()
    .split('\n')
    .map((row) => row.split(',').map((cell) => cell.trim()))
}

export function ProtectedFilesPage() {
  const currentUser = useAuthStore((state) => state.currentUser)
  const [selectedFile, setSelectedFile] = useState<ProtectedFile | null>(null)

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
    onSuccess: (data) => setSelectedFile(data.files[0] ?? null),
  })

  const fileContentQuery = useQuery({
    queryKey: ['protected-files', 'content', selectedFile?.id, localDeviceId],
    queryFn: () => protectedService.getFileContent(selectedFile!.id, Number(localDeviceId)),
    enabled: Boolean(selectedFile?.id && localDeviceId !== null && selectedFile.type === 'pdf'),
  })

  const pdfUrl = useMemo(() => {
    if (!fileContentQuery.data) return null
    return URL.createObjectURL(fileContentQuery.data)
  }, [fileContentQuery.data])

  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl)
    }
  }, [pdfUrl])

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

          <section className="grid grid-cols-[minmax(280px,0.9fr)_minmax(0,1.4fr)] gap-4 max-lg:grid-cols-1">
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
                    <tr
                      className={`cursor-pointer ${selectedFile?.name === file.name ? 'bg-zinc-50' : ''}`}
                      key={file.name}
                      onClick={() => setSelectedFile(file)}
                    >
                      <td className={tdClassName}>
                        <span className="font-semibold text-zinc-950">{file.name}</span>
                        <p className="mt-1 max-w-sm text-xs text-zinc-500">{file.summary}</p>
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

            <article className="ui-panel">
              {selectedFile ? (
                <>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="text-lg font-semibold text-zinc-950">{selectedFile.name}</h2>
                      <p className="mt-1 text-sm text-zinc-600">{selectedFile.summary}</p>
                    </div>
                    <StatusBadge tone={sensitivityTone(selectedFile.sensitivity)}>{selectedFile.sensitivity}</StatusBadge>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs text-zinc-500">
                    <span>Type: {selectedFile.type}</span>
                    <span>·</span>
                    <span>Size: {selectedFile.size}</span>
                  </div>
                  {selectedFile.type === 'pdf' && (
                    <div className="mt-5 overflow-hidden rounded-2xl border border-zinc-950/10 bg-zinc-100">
                      {fileContentQuery.isLoading && <LoadingState message="Loading PDF preview..." />}
                      {fileContentQuery.isError && <ErrorState message={getApiErrorMessage(fileContentQuery.error)} />}
                      {pdfUrl && <iframe className="h-[620px] w-full bg-white" src={pdfUrl} title={selectedFile.name} />}
                    </div>
                  )}

                  {selectedFile.type === 'csv' && selectedFile.content && (
                    <div className="mt-5 max-h-[520px] overflow-auto rounded-2xl border border-zinc-950/10">
                      <table className="min-w-full border-collapse text-left text-xs">
                        <thead className="sticky top-0 bg-zinc-100">
                          <tr>
                            {parseCsv(selectedFile.content)[0]?.map((header) => (
                              <th className="border-b border-zinc-950/10 px-3 py-2 font-semibold text-zinc-700" key={header}>{header}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {parseCsv(selectedFile.content).slice(1).map((row, rowIndex) => (
                            <tr key={`${selectedFile.name}-${rowIndex}`}>
                              {row.map((cell, cellIndex) => (
                                <td className="border-b border-zinc-950/5 px-3 py-2 text-zinc-700" key={cellIndex}>{cell}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {selectedFile.type !== 'pdf' && selectedFile.type !== 'csv' && selectedFile.content && (
                    <pre className="mt-5 max-h-[520px] overflow-auto whitespace-pre-wrap rounded-2xl border border-zinc-950/10 bg-zinc-950 p-4 font-mono text-xs leading-5 text-zinc-100">
                      {selectedFile.content}
                    </pre>
                  )}
                </>
              ) : (
                <p className="text-sm text-zinc-600">Select a file to preview its protected contents.</p>
              )}
            </article>
          </section>
        </section>
      )}
    </PageShell>
  )
}
