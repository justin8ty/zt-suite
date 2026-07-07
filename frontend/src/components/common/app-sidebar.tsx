import { NavLink } from 'react-router-dom'

import { useRole } from '@/hooks/use-role'
import { routes } from '@/lib/routes'

interface NavItem {
  label: string
  path: string
  adminOnly?: boolean
  securityOnly?: boolean
  signal?: 'neutral' | 'identity' | 'posture' | 'network' | 'alert' | 'audit'
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: routes.dashboard, signal: 'neutral' },
  { label: 'Devices', path: routes.devices, securityOnly: true, signal: 'posture' },
  { label: 'Flows', path: routes.flows, securityOnly: true, signal: 'network' },
  { label: 'Alerts', path: routes.alerts, securityOnly: true, signal: 'alert' },
  { label: 'Users', path: routes.users, adminOnly: true, signal: 'identity' },
  { label: 'Access Logs', path: routes.logs, adminOnly: true, signal: 'audit' },
  { label: 'Protected Files', path: routes.protectedFiles, signal: 'identity' },
  { label: 'Unauthorized', path: routes.unauthorized },
]

const signalClassNames: Record<NonNullable<NavItem['signal']>, string> = {
  neutral: 'bg-zinc-400',
  identity: 'bg-zinc-500',
  posture: 'bg-zinc-500',
  network: 'bg-zinc-500',
  alert: 'bg-zinc-500',
  audit: 'bg-zinc-500',
}

export function AppSidebar() {
  const { isAdmin, canViewSecurityData } = useRole()
  const visibleItems = navItems.filter((item) => {
    if (item.path === routes.unauthorized) {
      return false
    }

    if (item.adminOnly) {
      return isAdmin
    }

    if (item.securityOnly) {
      return canViewSecurityData
    }

    return true
  })

  return (
    <aside className="sticky top-4 h-[calc(100vh-2rem)] rounded-2xl border border-zinc-950/10 bg-zinc-950 p-4 text-white shadow-[0_18px_60px_rgba(15,23,42,0.22)] max-lg:static max-lg:h-auto">
      <div className="mb-7 flex items-center gap-3 px-1">
        <div className="grid size-10 place-items-center rounded-xl bg-white font-mono text-sm font-semibold text-zinc-950">
          ZT
        </div>
        <div>
          <strong className="block text-sm font-semibold tracking-[-0.012em] text-white">ZT Suite</strong>
          <span className="block font-mono text-[0.68rem] uppercase tracking-[0.16em] text-zinc-400">Security console</span>
        </div>
      </div>

      <nav className="grid gap-1.5 max-lg:grid-cols-2 max-sm:grid-cols-1" aria-label="Main navigation">
        {visibleItems.map((item) => (
          <NavLink
            className={({ isActive }) =>
              `group flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium no-underline transition-[background-color,color,transform] duration-150 ${
                isActive
                  ? 'bg-white text-zinc-950'
                  : 'text-zinc-400 [@media(hover:hover)]:hover:bg-white/8 [@media(hover:hover)]:hover:text-white'
              }`
            }
            key={item.path}
            to={item.path}
          >
            <span className={`size-1.5 rounded-full ${signalClassNames[item.signal ?? 'neutral']}`} />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
