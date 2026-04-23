import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserMe } from '@/types/user'

interface AuthState {
  currentUser: UserMe | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean

  setTokens: (access: string, refresh: string) => void
  setAccessToken: (token: string) => void
  setUser: (user: UserMe) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      currentUser: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true }),

      setAccessToken: (token) => set({ accessToken: token }),

      setUser: (user) => set({ currentUser: user }),

      logout: () =>
        set({
          currentUser: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'filmtracker-auth',
      // Only persist refresh token and user — access token is short-lived
      partialize: (state) => ({
        refreshToken: state.refreshToken,
        currentUser: state.currentUser,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
