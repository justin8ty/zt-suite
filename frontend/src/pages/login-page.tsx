import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { LoginForm } from '@/components/auth/login-form'
import { getApiErrorMessage } from '@/services/api-client'
import { authService, isMfaRequired } from '@/services/auth-service'
import { useAuthStore } from '@/stores/auth-store'
import { routes } from '@/lib/routes'

export function LoginPage() {
  const navigate = useNavigate()
  const setTokens = useAuthStore((state) => state.setTokens)
  const setMfaTempToken = useAuthStore((state) => state.setMfaTempToken)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleLogin(values: { email: string; password: string }) {
    setIsSubmitting(true)
    setError(null)

    try {
      const response = await authService.login(values)

      if (isMfaRequired(response)) {
        setMfaTempToken(response.temp_token)
        navigate(routes.mfa)
        return
      }

      setTokens(response)
      navigate(routes.dashboard)
    } catch (loginError) {
      setError(getApiErrorMessage(loginError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="eyebrow">Zero-Trust Security Suite</div>
        <h1>Sign in to ZT Suite</h1>
        <p className="muted">Authenticate before accessing the security dashboard.</p>
        <LoginForm error={error} isSubmitting={isSubmitting} onSubmit={handleLogin} />
        <p className="auth-footnote">
          Need a test account? Use the seeded admin or register through the API for now.
        </p>
        <Link className="subtle-link" to={routes.dashboard}>
          Back to dashboard
        </Link>
      </section>
    </main>
  )
}
