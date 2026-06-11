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
      <section className="rounded-2xl border border-red-700/15 bg-red-50 p-6 text-red-700">
        <p>Ask an administrator to assign the required role if you need access.</p>
        <Link className="mt-4 inline-block ui-link" to={routes.dashboard}>
          Return to dashboard
        </Link>
      </section>
    </PageShell>
  )
}
