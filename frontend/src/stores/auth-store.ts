import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { TokenResponse } from '@/types/auth'
import type { User } from '@/types/user'

interface AuthStore {
  accessToken: string | null
  refreshToken: string | null
  mfaTempToken: string | null
  currentUser: User | null
  isAuthenticated: boolean
  setTokens: (tokens: TokenResponse) => void
  setMfaTempToken: (token: string | null) => void
  setCurrentUser: (user: User | null) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      mfaTempToken: null,
      currentUser: null,
      isAuthenticated: false,
      setTokens: (tokens) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          mfaTempToken: null,
          isAuthenticated: true,
        }),
      setMfaTempToken: (token) => set({ mfaTempToken: token }),
      setCurrentUser: (user) => set({ currentUser: user }),
      clearAuth: () =>
        set({
          accessToken: null,
          refreshToken: null,
          mfaTempToken: null,
          currentUser: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'zt-suite-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        currentUser: state.currentUser,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
