import { useState, type FormEvent } from 'react'
import { z } from 'zod'

const loginSchema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

const inputClassName =
  'w-full rounded-xl border border-slate-400/30 bg-slate-950/60 px-3.5 py-3 text-slate-50 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-400/15 disabled:cursor-not-allowed disabled:opacity-60'
const labelClassName = 'grid gap-2 text-left text-sm font-bold text-slate-300'
const buttonClassName =
  'min-h-11 rounded-xl bg-gradient-to-br from-sky-400 to-green-400 px-5 font-bold text-slate-950 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0'

interface LoginFormProps {
  isSubmitting: boolean
  error: string | null
  onSubmit: (values: { email: string; password: string }) => Promise<void>
}

export function LoginForm({ isSubmitting, error, onSubmit }: LoginFormProps) {
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('changeme123')
  const [validationError, setValidationError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setValidationError(null)

    const result = loginSchema.safeParse({ email, password })
    if (!result.success) {
      setValidationError(result.error.issues[0]?.message ?? 'Invalid login details')
      return
    }

    await onSubmit(result.data)
  }

  return (
    <form className="mt-7 grid gap-4" onSubmit={handleSubmit} noValidate>
      <label className={labelClassName}>
        Email
        <input
          autoComplete="email"
          className={inputClassName}
          disabled={isSubmitting}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="admin@example.com"
          type="email"
          value={email}
        />
      </label>

      <label className={labelClassName}>
        Password
        <input
          autoComplete="current-password"
          className={inputClassName}
          disabled={isSubmitting}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Enter your password"
          type="password"
          value={password}
        />
      </label>

      {(validationError || error) && (
        <p className="rounded-xl border border-red-400/35 bg-red-950/30 px-3 py-2.5 text-left text-red-100" role="alert">
          {validationError ?? error}
        </p>
      )}

      <button className={buttonClassName} disabled={isSubmitting} type="submit">
        {isSubmitting ? 'Signing in...' : 'Sign in'}
      </button>
    </form>
  )
}
