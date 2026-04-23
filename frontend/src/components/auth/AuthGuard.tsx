import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

export function AuthGuard() {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return <Outlet />
}

export function GuestGuard() {
  const { isAuthenticated, currentUser } = useAuthStore()

  if (isAuthenticated) {
    if (currentUser && !currentUser.onboarding_complete) {
      return <Navigate to="/onboarding" replace />
    }
    return <Navigate to="/" replace />
  }
  return <Outlet />
}
