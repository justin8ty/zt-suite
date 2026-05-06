import { useState, type FormEvent } from 'react'
import { z } from 'zod'

const mfaSchema = z.object({
  code: z.string().regex(/^\d{6}$/, 'Enter the 6-digit authenticator code'),
})

interface MfaValidateFormProps {
  isSubmitting: boolean
  error: string | null
  onSubmit: (code: string) => Promise<void>
}

export function MfaValidateForm({ isSubmitting, error, onSubmit }: MfaValidateFormProps) {
  const [code, setCode] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setValidationError(null)

    const result = mfaSchema.safeParse({ code })
    if (!result.success) {
      setValidationError(result.error.issues[0]?.message ?? 'Invalid MFA code')
      return
    }

    await onSubmit(result.data.code)
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <label>
        Authenticator code
        <input
          autoComplete="one-time-code"
          disabled={isSubmitting}
          inputMode="numeric"
          maxLength={6}
          onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
          placeholder="123456"
          type="text"
          value={code}
        />
      </label>

      {(validationError || error) && (
        <p className="form-error" role="alert">
          {validationError ?? error}
        </p>
      )}

      <button disabled={isSubmitting} type="submit">
        {isSubmitting ? 'Verifying...' : 'Verify MFA'}
      </button>
    </form>
  )
}
