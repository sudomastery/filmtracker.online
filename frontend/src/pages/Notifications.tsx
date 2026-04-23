import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Bell, CheckCheck, Heart, UserPlus, Star, MessageSquare } from 'lucide-react'
import { notificationService } from '@/services/user.service'
import { Avatar } from '@/components/ui/Avatar'
import { formatRelativeTime } from '@/utils/helpers'

interface Notification {
  id: string
  type: 'follow' | 'like' | 'comment' | 'rating'
  is_read: boolean
  created_at: string
  actor: {
    username: string
    display_name: string | null
    avatar_url: string | null
  }
  meta?: {
    movie_title?: string
    movie_tmdb_id?: number
  }
}

const TYPE_ICON = {
  follow:  <UserPlus className="w-4 h-4 text-brand-400" />,
  like:    <Heart className="w-4 h-4 text-red-400" />,
  comment: <MessageSquare className="w-4 h-4 text-blue-400" />,
  rating:  <Star className="w-4 h-4 text-yellow-400" />,
}

const TYPE_MESSAGE = (n: Notification) => {
  switch (n.type) {
    case 'follow':  return 'started following you'
    case 'like':    return `liked your review of ${n.meta?.movie_title ?? 'a movie'}`
    case 'comment': return `commented on your review of ${n.meta?.movie_title ?? 'a movie'}`
    case 'rating':  return `rated ${n.meta?.movie_title ?? 'a movie'}`
    default:        return 'did something'
  }
}

export default function NotificationsPage() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery<{ items: Notification[]; unread_count: number }>({
    queryKey: ['notifications'],
    queryFn: () => notificationService.getAll().then(r => r.data),
  })

  const markAllMutation = useMutation({
    mutationFn: () => notificationService.markAllRead(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notifications-count'] })
    },
  })

  const markOneMutation = useMutation({
    mutationFn: (id: string) => notificationService.markRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notifications-count'] })
    },
  })

  const notifications: Notification[] = data?.items ?? []
  const unreadCount = data?.unread_count ?? 0

  return (
    <div>
      {/* Header */}
      <div className="sticky top-0 z-20 bg-surface/90 backdrop-blur border-b border-surface-border px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-bold text-white">Notifications</h1>
        {unreadCount > 0 && (
          <button
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
            className="flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 transition-colors"
          >
            <CheckCheck className="w-4 h-4" />
            Mark all read
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : notifications.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center px-4">
          <Bell className="w-10 h-10 text-gray-700 mb-3" />
          <p className="text-gray-300 font-semibold mb-1">No notifications yet</p>
          <p className="text-gray-500 text-sm">When someone follows you or interacts with your reviews, you'll see it here.</p>
        </div>
      ) : (
        <div className="divide-y divide-surface-border">
          {notifications.map(n => (
            <div
              key={n.id}
              onClick={() => {
                if (!n.is_read) markOneMutation.mutate(n.id)
              }}
              className={`flex items-start gap-3 px-4 py-3 transition-colors cursor-default ${
                !n.is_read ? 'bg-brand-600/5 hover:bg-brand-600/10' : 'hover:bg-surface-card/40'
              }`}
            >
              {/* Unread dot */}
              <div className="flex-shrink-0 mt-1">
                {!n.is_read ? (
                  <div className="w-2 h-2 rounded-full bg-brand-500" />
                ) : (
                  <div className="w-2 h-2" />
                )}
              </div>

              {/* Avatar + icon */}
              <div className="relative flex-shrink-0">
                <Link to={`/profile/${n.actor.username}`}>
                  <Avatar src={n.actor.avatar_url} username={n.actor.username} size="sm" />
                </Link>
                <div className="absolute -bottom-1 -right-1 bg-surface rounded-full p-0.5">
                  {TYPE_ICON[n.type] ?? TYPE_ICON.rating}
                </div>
              </div>

              {/* Text */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-300 leading-snug">
                  <Link
                    to={`/profile/${n.actor.username}`}
                    className="font-semibold text-white hover:underline"
                  >
                    {n.actor.display_name || n.actor.username}
                  </Link>{' '}
                  {TYPE_MESSAGE(n)}
                </p>
                <p className="text-xs text-gray-600 mt-0.5">{formatRelativeTime(n.created_at)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
