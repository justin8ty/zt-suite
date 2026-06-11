import { useState, type FormEvent } from 'react'
import { z } from 'zod'

const loginSchema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

const labelClassName = 'grid gap-2 text-left text-sm font-semibold text-zinc-700'

interface LoginFormProps {
  isSubmitting: boolean
  error: string | null
  onSubmit: (values: { email: string; password: string }) => Promise<void>
}

export function LoginForm({ isSubmitting, error, onSubmit }: LoginFormProps) {
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('admin123')
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
          className="ui-input w-full"
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
          className="ui-input w-full"
          disabled={isSubmitting}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Enter your password"
          type="password"
          value={password}
        />
      </label>

      {(validationError || error) && (
        <p className="rounded-xl border border-red-700/15 bg-red-50 px-3 py-2.5 text-left text-sm text-red-700" role="alert">
          {validationError ?? error}
        </p>
      )}

      <button className="ui-button-primary" disabled={isSubmitting} type="submit">
        {isSubmitting ? 'Signing in...' : 'Sign in'}
      </button>
    </form>
  )
}
