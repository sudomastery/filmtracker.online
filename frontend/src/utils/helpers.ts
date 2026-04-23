import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSecs < 60) return 'just now'
  if (diffMins < 60) return `${diffMins}m`
  if (diffHours < 24) return `${diffHours}h`
  if (diffDays < 7) return `${diffDays}d`

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return '–'
  return score.toFixed(1)
}

export function getAvatarUrl(user: { avatar_url?: string | null; username: string }): string {
  if (user.avatar_url) return user.avatar_url
  // Deterministic color avatar via DiceBear
  return `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(user.username)}&backgroundColor=a928d8`
}

export function getPosterUrl(posterUrl: string | null | undefined, size = 'w500'): string {
  if (!posterUrl) return '/placeholder-poster.svg'
  if (posterUrl.startsWith('http')) return posterUrl
  return `https://image.tmdb.org/t/p/${size}${posterUrl}`
}
