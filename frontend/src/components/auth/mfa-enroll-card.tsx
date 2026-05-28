import { useMutation, useQueryClient } from '@tanstack/react-query'
import QRCode from 'qrcode'
import { useEffect, useState, type FormEvent } from 'react'

import { ErrorState } from '@/components/common/error-state'
import { getApiErrorMessage } from '@/services/api-client'
import { authService } from '@/services/auth-service'

const inputClassName =
  'w-full rounded-xl border border-slate-400/30 bg-slate-950/60 px-3 py-2.5 text-slate-50 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/15'
const buttonClassName =
  'min-h-10 rounded-xl bg-gradient-to-br from-sky-400 to-green-400 px-4 font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60'

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
      setQrCodeDataUrl('')
      setQrCodeError('')
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
    <section className="rounded-3xl border border-yellow-400/30 bg-yellow-500/10 p-6 text-yellow-50 shadow-2xl shadow-black/30 backdrop-blur-xl">
      <h2 className="text-lg font-bold">MFA required</h2>
      <p className="mt-2 text-yellow-100/80">
        Protected files require MFA. Enroll with an authenticator app, then verify your 6-digit
        code.
      </p>

      {!enrollMutation.data && (
        <button className={`${buttonClassName} mt-5`} disabled={enrollMutation.isPending} onClick={() => enrollMutation.mutate()} type="button">
          {enrollMutation.isPending ? 'Starting enrollment...' : 'Start MFA enrollment'}
        </button>
      )}

      {enrollMutation.data && (
        <div className="mt-5 grid gap-4">
          <div className="grid gap-4 lg:grid-cols-[auto_1fr]">
            <div className="rounded-2xl border border-yellow-400/20 bg-slate-950/40 p-4">
              <div className="text-sm font-bold">Scan QR code</div>
              <p className="mt-1 text-sm text-yellow-100/70">Open Google Authenticator, Microsoft Authenticator, or 1Password and scan this code.</p>
              <div className="mt-4 flex min-h-[220px] items-center justify-center rounded-xl bg-white p-3">
                {qrCodeDataUrl ? (
                  <img alt="MFA authenticator QR code" className="h-[220px] w-[220px]" src={qrCodeDataUrl} />
                ) : (
                  <span className="text-center text-sm text-slate-500">Generating QR code...</span>
                )}
              </div>
              {qrCodeError && <p className="mt-2 text-sm text-red-200">{qrCodeError}</p>}
            </div>

            <div className="grid gap-4">
              <div className="rounded-2xl border border-yellow-400/20 bg-slate-950/40 p-4">
                <div className="text-sm font-bold">Manual setup key</div>
                <code className="mt-1 block break-all text-sm text-yellow-100">{enrollMutation.data.secret}</code>
              </div>
              <div className="rounded-2xl border border-yellow-400/20 bg-slate-950/40 p-4">
                <div className="text-sm font-bold">Provisioning URI</div>
                <code className="mt-1 block break-all text-xs text-yellow-100">
                  {enrollMutation.data.provisioning_uri}
                </code>
              </div>
            </div>
          </div>

          <form className="grid grid-cols-[1fr_auto] gap-3 max-sm:grid-cols-1" onSubmit={handleVerify}>
            <input
              className={inputClassName}
              inputMode="numeric"
              maxLength={6}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
              placeholder="123456"
              value={code}
            />
            <button className={buttonClassName} disabled={verifyMutation.isPending || code.length !== 6} type="submit">
              {verifyMutation.isPending ? 'Verifying...' : 'Verify'}
            </button>
          </form>
        </div>
      )}

      {enrollMutation.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(enrollMutation.error)} /></div>}
      {verifyMutation.isError && <div className="mt-4"><ErrorState message={getApiErrorMessage(verifyMutation.error)} /></div>}
      {verifyMutation.isSuccess && <p className="mt-4 font-bold text-green-200">MFA enabled successfully.</p>}
    </section>
  )
}
