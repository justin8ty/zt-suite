import { NavLink } from 'react-router-dom'

import { useRole } from '@/hooks/use-role'
import { routes } from '@/lib/routes'

interface NavItem {
  label: string
  path: string
  adminOnly?: boolean
  securityOnly?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: routes.dashboard },
  { label: 'Devices', path: routes.devices, securityOnly: true },
  { label: 'Traffic', path: routes.traffic, securityOnly: true },
  { label: 'Alerts', path: routes.alerts, securityOnly: true },
  { label: 'Users', path: routes.users, adminOnly: true },
  { label: 'Access Logs', path: routes.logs, adminOnly: true },
  { label: 'Protected Files', path: routes.protectedFiles },
]

export function AppSidebar() {
  const { isAdmin, canViewSecurityData } = useRole()
  const visibleItems = navItems.filter((item) => {
    if (item.adminOnly) {
      return isAdmin
    }

    if (item.securityOnly) {
      return canViewSecurityData
    }

    return true
  })

  return (
    <aside className="sticky top-4 h-[calc(100vh-2rem)] rounded-3xl border border-slate-400/20 bg-slate-900/80 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl max-lg:static max-lg:h-auto">
      <div className="mb-7 flex items-center gap-3">
        <div className="grid size-11 place-items-center rounded-2xl bg-gradient-to-br from-sky-400 to-green-400 font-black text-slate-950">
          ZT
        </div>
        <div>
          <strong className="block text-slate-50">ZT Suite</strong>
          <span className="block text-sm text-slate-400">Security Console</span>
        </div>
      </div>

      <nav className="grid gap-2 max-lg:grid-cols-2 max-sm:grid-cols-1" aria-label="Main navigation">
        {visibleItems.map((item) => (
          <NavLink
            className={({ isActive }) =>
              `rounded-2xl border px-3.5 py-3 text-slate-300 no-underline transition hover:border-sky-400/30 hover:bg-sky-400/10 hover:text-slate-50 ${
                isActive ? 'border-sky-400/30 bg-sky-400/10 text-slate-50' : 'border-transparent'
              }`
            }
            key={item.path}
            to={item.path}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
