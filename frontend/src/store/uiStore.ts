import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'dark' | 'light'
type Modal = 'rate-movie' | 'movie-detail' | null

interface UIState {
  theme: Theme
  sidebarOpen: boolean
  activeModal: Modal
  modalMovieTmdbId: number | null

  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  setSidebarOpen: (open: boolean) => void
  openRateModal: (tmdbId: number) => void
  closeModal: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      sidebarOpen: true,
      activeModal: null,
      modalMovieTmdbId: null,

      setTheme: (theme) => {
        set({ theme })
        document.documentElement.classList.toggle('dark', theme === 'dark')
      },

      toggleTheme: () => {
        const next = get().theme === 'dark' ? 'light' : 'dark'
        get().setTheme(next)
      },

      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      openRateModal: (tmdbId) =>
        set({ activeModal: 'rate-movie', modalMovieTmdbId: tmdbId }),

      closeModal: () => set({ activeModal: null, modalMovieTmdbId: null }),
    }),
    {
      name: 'filmtracker-ui',
      partialize: (state) => ({ theme: state.theme }),
    }
  )
)
