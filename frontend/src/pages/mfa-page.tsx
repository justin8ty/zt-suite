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

  async function handleValidate(code: string) {
    const activeTempToken = tempToken

    if (!activeTempToken) {
      navigate(routes.login)
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const tokens = await authService.validateMfa({ temp_token: activeTempToken, code })
      setTokens(tokens)
      navigate(routes.dashboard)
    } catch (mfaError) {
      setError(getApiErrorMessage(mfaError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="eyebrow">MFA Challenge</div>
        <h1>Enter your TOTP code</h1>
        <p className="muted">Use your authenticator app to complete login.</p>
        <MfaValidateForm error={error} isSubmitting={isSubmitting} onSubmit={handleValidate} />
      </section>
    </main>
  )
}
