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
    <aside className="app-sidebar">
      <div className="brand-block">
        <div className="brand-mark">ZT</div>
        <div>
          <strong>ZT Suite</strong>
          <span>Security Console</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        {visibleItems.map((item) => (
          <NavLink
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
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
