import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { LoginForm } from '@/components/auth/login-form'
import { routes } from '@/lib/routes'
import { getApiErrorMessage } from '@/services/api-client'
import { authService, isMfaRequired } from '@/services/auth-service'
import { useAuthStore } from '@/stores/auth-store'

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
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <main className="ui-auth-grid" id="main-content">
        <section className="ui-auth-card">
          <div className="ui-eyebrow mb-3">Zero-trust security suite</div>
          <h1 className="ui-title md:text-5xl">Sign in to ZT Suite</h1>
          <p className="ui-subtitle">Authenticate before accessing the security dashboard.</p>
        <LoginForm error={error} isSubmitting={isSubmitting} onSubmit={handleLogin} />
        <p className="mt-5 text-sm text-zinc-600">
          Need an account?{' '}
          <Link className="ui-link" to={routes.register}>
            Create one
          </Link>
        </p>
        <Link className="mt-3.5 inline-block ui-link" to={routes.dashboard}>
          Back to dashboard
        </Link>
        </section>
      </main>
    </>
  )
}
