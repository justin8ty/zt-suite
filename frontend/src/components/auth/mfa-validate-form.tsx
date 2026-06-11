import { useState, type FormEvent } from 'react'
import { z } from 'zod'

const mfaSchema = z.object({
  code: z.string().regex(/^\d{6}$/, 'Enter the 6-digit authenticator code'),
})

interface MfaValidateValues {
  code: string
  trustDevice: boolean
}

interface MfaValidateFormProps {
  isSubmitting: boolean
  error: string | null
  onSubmit: (values: MfaValidateValues) => Promise<void>
}

export function MfaValidateForm({ isSubmitting, error, onSubmit }: MfaValidateFormProps) {
  const [code, setCode] = useState('')
  const [trustDevice, setTrustDevice] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setValidationError(null)

    const result = mfaSchema.safeParse({ code })
    if (!result.success) {
      setValidationError(result.error.issues[0]?.message ?? 'Invalid MFA code')
      return
    }

    await onSubmit({ code: result.data.code, trustDevice })
  }

  return (
    <form className="mt-7 grid gap-4" onSubmit={handleSubmit} noValidate>
      <label className="grid gap-2 text-left text-sm font-semibold text-zinc-700">
        Authenticator code
        <input
          autoComplete="one-time-code"
          className="ui-input w-full font-mono tracking-[0.18em]"
          disabled={isSubmitting}
          inputMode="numeric"
          maxLength={6}
          onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
          placeholder="123456"
          type="text"
          value={code}
        />
      </label>

      <label className="flex items-start gap-3 rounded-xl border border-zinc-950/10 bg-zinc-50 p-3 text-left text-sm text-zinc-600">
        <input
          checked={trustDevice}
          className="mt-1 size-4 accent-zinc-950"
          disabled={isSubmitting}
          onChange={(event) => setTrustDevice(event.target.checked)}
          type="checkbox"
        />
        <span>
          <span className="block font-semibold text-zinc-900">Trust this device for 30 days</span>
          <span className="block text-zinc-600">Skip MFA on this browser after password login.</span>
        </span>
      </label>

      {(validationError || error) && (
        <p className="rounded-xl border border-red-700/15 bg-red-50 px-3 py-2.5 text-left text-sm text-red-700" role="alert">
          {validationError ?? error}
        </p>
      )}

      <button className="ui-button-primary" disabled={isSubmitting} type="submit">
        {isSubmitting ? 'Verifying...' : 'Verify MFA'}
      </button>
    </form>
  )
}
