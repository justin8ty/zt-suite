import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { MfaValidateForm } from '@/components/auth/mfa-validate-form'
import { routes } from '@/lib/routes'
import { getApiErrorMessage } from '@/services/api-client'
import { authService } from '@/services/auth-service'
import { useAuthStore } from '@/stores/auth-store'

export function MfaPage() {
  const navigate = useNavigate()
  const tempToken = useAuthStore((state) => state.mfaTempToken)
  const setTokens = useAuthStore((state) => state.setTokens)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!tempToken) {
    return <Navigate replace to={routes.login} />
  }

  async function handleValidate(values: { code: string; trustDevice: boolean }) {
    const activeTempToken = tempToken

    if (!activeTempToken) {
      navigate(routes.login)
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const tokens = await authService.validateMfa({
        temp_token: activeTempToken,
        code: values.code,
        trust_device: values.trustDevice,
        device_label: window.navigator.userAgent,
      })
      setTokens(tokens)
      navigate(routes.dashboard)
    } catch (mfaError) {
      setError(getApiErrorMessage(mfaError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4 py-8">
      <section className="w-full max-w-md rounded-[1.75rem] border border-slate-400/20 bg-slate-900/80 p-8 shadow-2xl shadow-black/30 backdrop-blur-xl">
        <div className="mb-3.5 text-xs font-extrabold tracking-[0.18em] text-cyan-300 uppercase">
          MFA Challenge
        </div>
        <h1 className="text-4xl leading-none font-bold tracking-tight text-slate-50 md:text-5xl">
          Enter your TOTP code
        </h1>
        <p className="mt-3.5 text-slate-400">Use your authenticator app to complete login.</p>
        <MfaValidateForm error={error} isSubmitting={isSubmitting} onSubmit={handleValidate} />
      </section>
    </main>
  )
}
