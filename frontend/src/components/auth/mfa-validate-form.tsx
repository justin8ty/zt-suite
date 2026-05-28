import { useState, type FormEvent } from 'react'
import { z } from 'zod'

const mfaSchema = z.object({
  code: z.string().regex(/^\d{6}$/, 'Enter the 6-digit authenticator code'),
})

const inputClassName =
  'w-full rounded-xl border border-slate-400/30 bg-slate-950/60 px-3.5 py-3 text-slate-50 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-400/15 disabled:cursor-not-allowed disabled:opacity-60'
const buttonClassName =
  'min-h-11 rounded-xl bg-gradient-to-br from-sky-400 to-green-400 px-5 font-bold text-slate-950 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0'

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
      <label className="grid gap-2 text-left text-sm font-bold text-slate-300">
        Authenticator code
        <input
          autoComplete="one-time-code"
          className={inputClassName}
          disabled={isSubmitting}
          inputMode="numeric"
          maxLength={6}
          onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
          placeholder="123456"
          type="text"
          value={code}
        />
      </label>

      <label className="flex items-start gap-3 rounded-xl border border-slate-400/20 bg-slate-950/40 p-3 text-left text-sm text-slate-300">
        <input
          checked={trustDevice}
          className="mt-1 h-4 w-4 rounded border-slate-500 bg-slate-950 text-cyan-300"
          disabled={isSubmitting}
          onChange={(event) => setTrustDevice(event.target.checked)}
          type="checkbox"
        />
        <span>
          <span className="block font-bold text-slate-200">Trust this device for 30 days</span>
          <span className="block text-slate-400">Skip MFA on this browser after password login.</span>
        </span>
      </label>

      {(validationError || error) && (
        <p className="rounded-xl border border-red-400/35 bg-red-950/30 px-3 py-2.5 text-left text-red-100" role="alert">
          {validationError ?? error}
        </p>
      )}

      <button className={buttonClassName} disabled={isSubmitting} type="submit">
        {isSubmitting ? 'Verifying...' : 'Verify MFA'}
      </button>
    </form>
  )
}
