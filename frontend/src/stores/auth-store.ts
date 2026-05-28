import { create } from 'zustand'

import type { TokenResponse } from '@/types/auth'
import type { User } from '@/types/user'

if (typeof window !== 'undefined') {
  window.localStorage.removeItem('zt-suite-auth')
}

interface AuthStore {
  accessToken: string | null
  mfaTempToken: string | null
  currentUser: User | null
  isAuthenticated: boolean
  setTokens: (tokens: TokenResponse) => void
  setMfaTempToken: (token: string | null) => void
  setCurrentUser: (user: User | null) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthStore>()((set) => ({
  accessToken: null,
  mfaTempToken: null,
  currentUser: null,
  isAuthenticated: false,
  setTokens: (tokens) =>
    set({
      accessToken: tokens.access_token,
      mfaTempToken: null,
      isAuthenticated: true,
    }),
  setMfaTempToken: (token) => set({ mfaTempToken: token }),
  setCurrentUser: (user) => set({ currentUser: user }),
  clearAuth: () =>
    set({
      accessToken: null,
      mfaTempToken: null,
      currentUser: null,
      isAuthenticated: false,
    }),
}))
