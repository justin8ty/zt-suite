import { useMutation, useQueryClient } from '@tanstack/react-query'
import QRCode from 'qrcode'
import { useEffect, useState, type FormEvent } from 'react'

import { ErrorState } from '@/components/common/error-state'
import { getApiErrorMessage } from '@/services/api-client'
import { authService } from '@/services/auth-service'

export function MfaEnrollCard() {
  const queryClient = useQueryClient()
  const [code, setCode] = useState('')
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState('')
  const [qrCodeError, setQrCodeError] = useState('')

  const enrollMutation = useMutation({
    mutationFn: authService.enrollMfa,
  })

  const verifyMutation = useMutation({
    mutationFn: () => authService.verifyMfa({ code }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth', 'me'] }),
  })

  useEffect(() => {
    const provisioningUri = enrollMutation.data?.provisioning_uri
    if (!provisioningUri) {
      return
    }

    let isCurrent = true
    QRCode.toDataURL(provisioningUri, { margin: 1, width: 220 })
      .then((dataUrl) => {
        if (isCurrent) {
          setQrCodeDataUrl(dataUrl)
          setQrCodeError('')
        }
      })
      .catch(() => {
        if (isCurrent) {
          setQrCodeDataUrl('')
          setQrCodeError('Could not generate QR code. Use the secret below instead.')
        }
      })

    return () => {
      isCurrent = false
    }
  }, [enrollMutation.data?.provisioning_uri])

  async function handleVerify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await verifyMutation.mutateAsync()
  }

  return (
    <section className="rounded-2xl border border-amber-700/15 bg-amber-50 p-5 text-amber-900">
      <h2 className="ui-section-title text-amber-950">MFA required</h2>
      <p className="mt-2 text-sm leading-6 text-amber-800">
        Protected files require MFA. Enroll with an authenticator app, then verify your 6-digit code.
      </p>

      {!enrollMutation.data && (
        <button className="ui-button-primary mt-5" disabled={enrollMutation.isPending} onClick={() => enrollMutation.mutate()} type="button">
          {enrollMutation.isPending ? 'Starting enrollment...' : 'Start MFA enrollment'}
        </button>
      )}

      {enrollMutation.data && (
        <div className="mt-5 grid gap-4">
          <div className="grid gap-4 lg:grid-cols-[auto_1fr]">
            <div className="rounded-2xl border border-amber-700/15 bg-white p-4">
              <div className="text-sm font-semibold text-zinc-950">Scan QR code</div>
              <p className="mt-1 text-sm text-zinc-600">Open Google Authenticator, Microsoft Authenticator, or 1Password and scan this code.</p>
              <div className="mt-4 flex min-h-[220px] items-center justify-center rounded-xl bg-white p-3 shadow-inner ring-1 ring-zinc-950/10">
                {qrCodeDataUrl ? (
                  <img alt="MFA authenticator QR code" className="h-[220px] w-[220px]" src={qrCodeDataUrl} />
                ) : (
                  <span className="text-center text-sm text-zinc-500">Generating QR code...</span>
                )}
              </div>
              {qrCodeError && <p className="mt-2 text-sm text-red-700">{qrCodeError}</p>}
            </div>

            <div className="grid gap-4">
              <div className="rounded-2xl border border-zinc-950/10 bg-white p-4">
                <div className="text-sm font-semibold text-zinc-950">Manual setup key</div>
                <code className="ui-terminal mt-2 block break-all">{enrollMutation.data.secret}</code>
              </div>
              <div className="rounded-2xl border border-zinc-950/10 bg-white p-4">
                <div className="text-sm font-semibold text-zinc-950">Provisioning URI</div>
                <code className="ui-terminal mt-2 block break-all">
                  {enrollMutation.data.provisioning_uri}
                </code>
              </div>
            </div>
          </div>

          <form className="grid grid-cols-[1fr_auto] gap-3 max-sm:grid-cols-1" onSubmit={handleVerify}>
            <input
              className="ui-input font-mono tracking-[0.18em]"
              inputMode="numeric"
              maxLength={6}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
              placeholder="123456"
              value={code}
            />
            <button className="ui-button-primary" disabled={verifyMutation.isPending || code.length !== 6} type="submit">
              {verifyMutation.isPending ? 'Verifying...' : 'Verify'}
            </button>
          </form>
        </div>
      )}

      {enrollMutation.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(enrollMutation.error)} /></div>}
      {verifyMutation.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(verifyMutation.error)} /></div>}
      {verifyMutation.isSuccess && <p className="mt-4 font-semibold text-emerald-700">MFA enabled successfully.</p>}
    </section>
  )
}
