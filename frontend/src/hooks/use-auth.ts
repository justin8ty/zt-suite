import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { authService } from '@/services/auth-service'
import { useAuthStore } from '@/stores/auth-store'

export function useCurrentUser() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const setCurrentUser = useAuthStore((state) => state.setCurrentUser)

  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const user = await authService.getMe()
      setCurrentUser(user)
      return user
    },
    enabled: isAuthenticated,
    staleTime: 60_000,
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const refreshToken = useAuthStore((state) => state.refreshToken)
  const clearAuth = useAuthStore((state) => state.clearAuth)

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await authService.logout({ refresh_token: refreshToken })
      }
    },
    onSettled: () => {
      clearAuth()
      queryClient.clear()
    },
  })
}
