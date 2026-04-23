import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Film, Users, Star } from 'lucide-react'
import { userService } from '@/services/user.service'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'
import { Avatar } from '@/components/ui/Avatar'
import { FollowButton } from '@/components/profile/FollowButton'
import { getPosterUrl } from '@/utils/helpers'
import type { UserProfile } from '@/types/user'

interface RatingEntry {
  id: string
  score: number | null
  review: string | null
  watched_on: string | null
  created_at: string
  movie: {
    tmdb_id: number
    title: string
    poster_url: string | null
    release_year: number | null
  }
}

export default function Profile() {
  const { username } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const { currentUser } = useAuthStore()
  const { openRateModal } = useUIStore()
  const qc = useQueryClient()
  const isOwnProfile = currentUser?.username === username

  const { data: profile, isLoading } = useQuery<UserProfile>({
    queryKey: ['profile', username],
    queryFn: () => userService.getProfile(username!).then(r => r.data),
    enabled: !!username,
  })

  const { data: ratingsData } = useQuery<{ items: RatingEntry[] }>({
    queryKey: ['user-ratings', username],
    queryFn: () => userService.getUserRatings(username!).then(r => r.data),
    enabled: !!username,
  })

  const ratings: RatingEntry[] = ratingsData?.items ?? []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center px-4">
        <p className="text-gray-400">User not found.</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-brand-400 hover:underline text-sm">
          Go back
        </button>
      </div>
    )
  }

  return (
    <div className="pb-8">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-surface/90 backdrop-blur border-b border-surface-border px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-base font-bold text-white truncate">
          {profile.display_name || profile.username}
        </h1>
      </div>

      {/* Profile header */}
      <div className="px-4 py-5 border-b border-surface-border">
        <div className="flex items-start justify-between gap-4">
          <Avatar src={profile.avatar_url} username={profile.username} size="xl" />

          <div className="flex-shrink-0">
            {isOwnProfile ? (
              <button
                className="px-4 py-1.5 rounded-xl border border-surface-border text-sm font-medium text-gray-300 hover:bg-surface-muted transition-colors"
                onClick={() => {/* TODO: edit profile modal */}}
              >
                Edit profile
              </button>
            ) : (
              <FollowButton
                username={profile.username}
                isFollowing={profile.is_following}
                onToggle={() => {
                  qc.invalidateQueries({ queryKey: ['profile', username] })
                }}
              />
            )}
          </div>
        </div>

        <div className="mt-3 space-y-1">
          <h2 className="text-lg font-bold text-white">
            {profile.display_name || profile.username}
          </h2>
          <p className="text-sm text-gray-500">@{profile.username}</p>
          {profile.bio && (
            <p className="text-sm text-gray-300 leading-relaxed pt-1">{profile.bio}</p>
          )}
        </div>

        {/* Stats row */}
        <div className="flex gap-6 mt-4">
          <div className="flex items-center gap-1.5">
            <Star className="w-4 h-4 text-brand-400" />
            <span className="font-semibold text-white text-sm">{profile.rating_count}</span>
            <span className="text-gray-500 text-sm">ratings</span>
          </div>
          <button
            className="flex items-center gap-1.5 hover:underline"
            onClick={() => navigate(`/profile/${username}/following`)}
          >
            <Users className="w-4 h-4 text-gray-400" />
            <span className="font-semibold text-white text-sm">{profile.following_count}</span>
            <span className="text-gray-500 text-sm">following</span>
          </button>
          <button
            className="flex items-center gap-1.5 hover:underline"
            onClick={() => navigate(`/profile/${username}/followers`)}
          >
            <span className="font-semibold text-white text-sm">{profile.follower_count}</span>
            <span className="text-gray-500 text-sm">followers</span>
          </button>
        </div>
      </div>

      {/* Ratings grid */}
      <div className="px-4 py-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Film className="w-4 h-4" />
          Rated Movies
        </h3>

        {ratings.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 text-sm">
              {isOwnProfile ? "You haven't rated any movies yet." : 'No ratings yet.'}
            </p>
            {isOwnProfile && (
              <button
                onClick={() => openRateModal(0)}
                className="mt-3 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-xl transition-colors"
              >
                Rate a movie
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
            {ratings.map(r => (
              <button
                key={r.id}
                onClick={() => navigate(`/movie/${r.movie.tmdb_id}`)}
                className="relative group rounded-xl overflow-hidden bg-surface-muted aspect-[2/3]"
              >
                <img
                  src={getPosterUrl(r.movie.poster_url, 'w185')}
                  alt={r.movie.title}
                  className="w-full h-full object-cover group-hover:opacity-80 transition-opacity"
                  onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
                />
                {r.score !== null && (
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-1.5 pb-1.5 pt-4">
                    <div className="flex items-center gap-0.5">
                      <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                      <span className="text-xs text-white font-medium">{r.score}</span>
                    </div>
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
