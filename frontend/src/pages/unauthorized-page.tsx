import { Link } from 'react-router-dom'

import { PageShell } from '@/components/common/page-shell'
import { routes } from '@/lib/routes'

export function UnauthorizedPage() {
  return (
    <PageShell
      description="Your current role does not have permission to open this dashboard area."
      eyebrow="Access denied"
      title="Unauthorized"
    >
      <section className="rounded-3xl border border-red-400/30 bg-red-500/10 p-6 text-red-100 shadow-2xl shadow-black/30 backdrop-blur-xl">
        <p>Ask an administrator to assign the required role if you need access.</p>
        <Link className="mt-4 inline-block font-bold text-cyan-300 hover:text-cyan-200" to={routes.dashboard}>
          Return to dashboard
        </Link>
      </section>
    </PageShell>
  )
}
