import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Home, Compass, Bell, Bookmark, Upload, User, LogOut, Sun, Moon, Film, Menu, X } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'
import { Avatar } from './Avatar'
import { Button } from './Button'
import { RateMovieModal } from '@/components/movie/RateMovieModal'
import { TrendingPanel } from '@/components/feed/TrendingPanel'
import { cn } from '@/utils/helpers'
import { useQuery } from '@tanstack/react-query'
import { notificationService } from '@/services/user.service'
import { useState } from 'react'

const navItems = [
  { to: '/',              icon: Home,     label: 'Home' },
  { to: '/explore',       icon: Compass,  label: 'Explore' },
  { to: '/notifications', icon: Bell,     label: 'Notifications' },
  { to: '/watchlist',     icon: Bookmark, label: 'Watchlist' },
  { to: '/import',        icon: Upload,   label: 'Import' },
]

export function AppLayout() {
  const { currentUser, logout } = useAuthStore()
  const { theme, toggleTheme, activeModal } = useUIStore()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const { data: notifData } = useQuery({
    queryKey: ['notifications-count'],
    queryFn: () => notificationService.getAll().then(r => r.data),
    refetchInterval: 30000,
  })
  const unreadCount = notifData?.unread_count ?? 0

  const handleLogout = () => {
    const { refreshToken } = useAuthStore.getState()
    if (refreshToken) {
      import('@/services/auth.service').then(({ authService }) => {
        authService.logout(refreshToken).catch(() => {})
      })
    }
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-surface flex">
      {/* ── Sidebar (desktop) ── */}
      <aside className="hidden lg:flex flex-col fixed left-0 top-0 h-full w-64 border-r border-surface-border px-4 py-6 z-40">
        {/* Logo */}
        <div className="flex items-center gap-2 px-2 mb-8">
          <Film className="w-7 h-7 text-brand-500" />
          <span className="text-xl font-bold text-white">FilmTracker</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors relative',
                  isActive
                    ? 'bg-brand-600/20 text-brand-400'
                    : 'text-gray-400 hover:bg-surface-muted hover:text-white'
                )
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {label}
              {label === 'Notifications' && unreadCount > 0 && (
                <span className="ml-auto bg-brand-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </NavLink>
          ))}

          {currentUser && (
            <NavLink
              to={`/profile/${currentUser.username}`}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-600/20 text-brand-400'
                    : 'text-gray-400 hover:bg-surface-muted hover:text-white'
                )
              }
            >
              <User className="w-5 h-5 flex-shrink-0" />
              Profile
            </NavLink>
          )}
        </nav>

        {/* Rate a Movie CTA */}
        <Button
          className="w-full mb-6"
          onClick={() => useUIStore.getState().openRateModal(0)}
        >
          + Rate a Movie
        </Button>

        {/* User footer */}
        {currentUser && (
          <div className="flex items-center gap-3 px-2">
            <Avatar src={currentUser.avatar_url} username={currentUser.username} size="sm" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {currentUser.display_name || currentUser.username}
              </p>
              <p className="text-xs text-gray-500 truncate">@{currentUser.username}</p>
            </div>
            <div className="flex gap-1">
              <button onClick={toggleTheme} className="p-1.5 rounded-lg hover:bg-surface-muted text-gray-500 hover:text-white transition-colors">
                {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button onClick={handleLogout} className="p-1.5 rounded-lg hover:bg-surface-muted text-gray-500 hover:text-red-400 transition-colors">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 lg:ml-64 xl:mr-80 min-h-screen">
        <div className="max-w-2xl mx-auto">
          {/* Mobile topbar */}
          <div className="lg:hidden sticky top-0 z-30 bg-surface/90 backdrop-blur border-b border-surface-border px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Film className="w-6 h-6 text-brand-500" />
              <span className="font-bold text-white">FilmTracker</span>
            </div>
            <button onClick={() => setMobileMenuOpen(v => !v)} className="text-gray-400 hover:text-white">
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

          {/* Mobile drawer */}
          {mobileMenuOpen && (
            <div className="lg:hidden fixed inset-0 z-50 bg-surface/95 backdrop-blur p-6" onClick={() => setMobileMenuOpen(false)}>
              <div className="flex items-center gap-2 mb-8">
                <Film className="w-7 h-7 text-brand-500" />
                <span className="text-xl font-bold text-white">FilmTracker</span>
              </div>
              <nav className="space-y-2">
                {navItems.map(({ to, icon: Icon, label }) => (
                  <NavLink key={to} to={to} end={to === '/'} onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) => cn('flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium', isActive ? 'bg-brand-600/20 text-brand-400' : 'text-gray-300')}
                  >
                    <Icon className="w-5 h-5" />{label}
                  </NavLink>
                ))}
              </nav>
              <Button className="w-full mt-6" onClick={() => { useUIStore.getState().openRateModal(0); setMobileMenuOpen(false) }}>
                + Rate a Movie
              </Button>
              <button onClick={handleLogout} className="mt-4 flex items-center gap-2 text-red-400 px-4 py-2">
                <LogOut className="w-4 h-4" /> Sign out
              </button>
            </div>
          )}

          <Outlet />
        </div>
      </main>

      {/* ── Right panel (desktop) ── */}
      <aside className="hidden xl:flex flex-col fixed right-0 top-0 h-full w-80 border-l border-surface-border px-4 py-6 overflow-y-auto">
        <TrendingPanel />
      </aside>

      {/* Global Rate Movie Modal */}
      {activeModal === 'rate-movie' && <RateMovieModal />}
    </div>
  )
}
