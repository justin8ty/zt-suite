import { Outlet } from 'react-router-dom'

import { AppHeader } from '@/components/common/app-header'
import { AppSidebar } from '@/components/common/app-sidebar'
import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { useCurrentUser } from '@/hooks/use-auth'
import { getApiErrorMessage } from '@/services/api-client'

export function DashboardLayout() {
  const currentUserQuery = useCurrentUser()

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <div className="ui-shell">
        <AppSidebar />
        <div className="min-w-0">
          <AppHeader />
          {currentUserQuery.isLoading && <LoadingState message="Loading session..." />}
          {currentUserQuery.isError && <ErrorState message={getApiErrorMessage(currentUserQuery.error)} />}
          {!currentUserQuery.isLoading && !currentUserQuery.isError && <Outlet />}
        </div>
      </div>
    </>
  )
}
