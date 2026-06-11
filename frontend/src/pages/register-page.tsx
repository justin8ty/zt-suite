import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { routes } from '@/lib/routes'
import { getApiErrorMessage } from '@/services/api-client'
import { authService, isMfaRequired } from '@/services/auth-service'
import { userService } from '@/services/user-service'
import { useAuthStore } from '@/stores/auth-store'

const registerSchema = z
  .object({
    email: z.email('Enter a valid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters').max(128, 'Password must be 128 characters or fewer'),
    confirmPassword: z.string().min(1, 'Confirm your password'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

const inputClassName = 'ui-input w-full'
const labelClassName = 'grid gap-2 text-left text-sm font-semibold text-zinc-700'
const buttonClassName =
  'ui-button-primary'

export function RegisterPage() {
  const navigate = useNavigate()
  const setTokens = useAuthStore((state) => state.setTokens)
  const setMfaTempToken = useAuthStore((state) => state.setMfaTempToken)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    const result = registerSchema.safeParse({ email, password, confirmPassword })
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? 'Invalid registration details')
      return
    }

    setIsSubmitting(true)

    try {
      await userService.create({ email: result.data.email, password: result.data.password })
      const loginResponse = await authService.login({ email: result.data.email, password: result.data.password })

      if (isMfaRequired(loginResponse)) {
        setMfaTempToken(loginResponse.temp_token)
        navigate(routes.mfa)
        return
      }

      setTokens(loginResponse)
      navigate(routes.dashboard)
    } catch (registerError) {
      setError(getApiErrorMessage(registerError))
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
          <h1 className="ui-title md:text-5xl">Create your ZT Suite account</h1>
          <p className="ui-subtitle">Register a standard user account, then continue directly into the dashboard.</p>

        <form className="mt-7 grid gap-4" onSubmit={handleSubmit} noValidate>
          <label className={labelClassName}>
            Email
            <input
              autoComplete="email"
              className={inputClassName}
              disabled={isSubmitting}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              type="email"
              value={email}
            />
          </label>

          <label className={labelClassName}>
            Password
            <input
              autoComplete="new-password"
              className={inputClassName}
              disabled={isSubmitting}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              type="password"
              value={password}
            />
          </label>

          <label className={labelClassName}>
            Confirm password
            <input
              autoComplete="new-password"
              className={inputClassName}
              disabled={isSubmitting}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Repeat your password"
              type="password"
              value={confirmPassword}
            />
          </label>

          {error && (
            <p
              className="rounded-xl border border-red-700/15 bg-red-50 px-3 py-2.5 text-left text-red-700"
              role="alert"
            >
              {error}
            </p>
          )}

          <button className={buttonClassName} disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="mt-5 text-sm text-zinc-600">
          Already have an account?{' '}
          <Link className="ui-link" to={routes.login}>
            Sign in
          </Link>
        </p>
        </section>
      </main>
    </>
  )
}
