import { useState, type FormEvent } from 'react'
import { z } from 'zod'

const loginSchema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

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
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <label>
        Email
        <input
          autoComplete="email"
          disabled={isSubmitting}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="admin@example.com"
          type="email"
          value={email}
        />
      </label>

      <label>
        Password
        <input
          autoComplete="current-password"
          disabled={isSubmitting}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Enter your password"
          type="password"
          value={password}
        />
      </label>

      {(validationError || error) && (
        <p className="form-error" role="alert">
          {validationError ?? error}
        </p>
      )}

      <button disabled={isSubmitting} type="submit">
        {isSubmitting ? 'Signing in...' : 'Sign in'}
      </button>
    </form>
  )
}
