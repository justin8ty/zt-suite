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
    <div className="app-shell">
      <AppSidebar />
      <div className="app-main">
        <AppHeader />
        {currentUserQuery.isLoading && <LoadingState message="Loading session..." />}
        {currentUserQuery.isError && <ErrorState message={getApiErrorMessage(currentUserQuery.error)} />}
        {!currentUserQuery.isLoading && !currentUserQuery.isError && <Outlet />}
      </div>
    </div>
  )
}
