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
    <main className="grid min-h-screen place-items-center px-4 py-8">
      <section className="w-full max-w-md rounded-[1.75rem] border border-slate-400/20 bg-slate-900/80 p-8 shadow-2xl shadow-black/30 backdrop-blur-xl">
        <div className="mb-3.5 text-xs font-extrabold tracking-[0.18em] text-cyan-300 uppercase">
          Zero-Trust Security Suite
        </div>
        <h1 className="text-4xl leading-none font-bold tracking-tight text-slate-50 md:text-5xl">
          Sign in to ZT Suite
        </h1>
        <p className="mt-3.5 text-slate-400">Authenticate before accessing the security dashboard.</p>
        <LoginForm error={error} isSubmitting={isSubmitting} onSubmit={handleLogin} />
        <p className="mt-5 text-sm text-slate-400">
          Need a test account? Use the seeded admin or register through the API for now.
        </p>
        <Link className="mt-3.5 inline-block text-cyan-300 no-underline hover:text-cyan-200" to={routes.dashboard}>
          Back to dashboard
        </Link>
      </section>
    </main>
  )
}
