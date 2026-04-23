import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'
import { authService } from '@/services/auth.service'
import { AppLayout } from '@/components/ui/AppLayout'
import { AuthGuard } from '@/components/auth/AuthGuard'
import { GuestGuard } from '@/components/auth/AuthGuard'

// Pages
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Onboarding from '@/pages/Onboarding'
import Home from '@/pages/Home'
import Explore from '@/pages/Explore'
import Profile from '@/pages/Profile'
import MoviePage from '@/pages/Movie'
import WatchlistPage from '@/pages/Watchlist'
import ImportPage from '@/pages/Import'
import NotificationsPage from '@/pages/Notifications'

export default function App() {
  const { isAuthenticated, setUser, refreshToken, setAccessToken, logout } = useAuthStore()
  const { theme } = useUIStore()

  // Apply theme class on mount
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  // Rehydrate user on mount if we have a refresh token
  useEffect(() => {
    if (!isAuthenticated || !refreshToken) return
    authService.getMe()
      .then(r => setUser(r.data))
      .catch(() => {
        // Try silent refresh first
        import('@/services/auth.service').then(({ authService: svc }) => {
          svc.refresh(refreshToken!)
            .then(r => {
              setAccessToken(r.data.access_token)
              return svc.getMe()
            })
            .then(r => setUser(r.data))
            .catch(() => logout())
        })
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        {/* Public auth routes */}
        <Route element={<GuestGuard />}>
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>

        {/* Onboarding (auth required, not yet complete) */}
        <Route element={<AuthGuard />}>
          <Route path="/onboarding" element={<Onboarding />} />
        </Route>

        {/* Main app routes inside layout */}
        <Route element={<AuthGuard />}>
          <Route element={<AppLayout />}>
            <Route path="/"              element={<Home />} />
            <Route path="/explore"       element={<Explore />} />
            <Route path="/movie/:tmdbId" element={<MoviePage />} />
            <Route path="/profile/:username" element={<Profile />} />
            <Route path="/watchlist"     element={<WatchlistPage />} />
            <Route path="/import"        element={<ImportPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
