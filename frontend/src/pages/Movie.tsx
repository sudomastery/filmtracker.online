import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Star, Clock, Calendar, Bookmark, BookmarkCheck, Play } from 'lucide-react'
import { movieService, watchlistService, ratingService } from '@/services/movie.service'
import { useUIStore } from '@/store/uiStore'
import { Avatar } from '@/components/ui/Avatar'
import { StarRating } from '@/components/ui/StarRating'
import { getPosterUrl, formatRelativeTime, cn } from '@/utils/helpers'
import type { Movie } from '@/types/movie'
import toast from 'react-hot-toast'

interface RatingEntry {
  id: string
  score: number | null
  review: string | null
  contains_spoiler: boolean
  watched_on: string | null
  created_at: string
  user: {
    id: string
    username: string
    display_name: string | null
    avatar_url: string | null
  }
}

export default function MoviePage() {
  const { tmdbId } = useParams<{ tmdbId: string }>()
  const navigate = useNavigate()
  const { openRateModal } = useUIStore()
  const qc = useQueryClient()
  const id = Number(tmdbId)

  const { data: movie, isLoading } = useQuery<Movie>({
    queryKey: ['movie', id],
    queryFn: () => movieService.getMovie(id).then(r => r.data),
    enabled: !!id,
  })

  const { data: ratingsData } = useQuery<{ items: RatingEntry[]; total: number }>({
    queryKey: ['movie-ratings', id],
    queryFn: () => movieService.getMovieRatings(id).then(r => r.data),
    enabled: !!id,
  })

  const { data: watchlist } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => watchlistService.getWatchlist().then(r => r.data),
  })

  const watchlistItem = watchlist?.find((w: any) => w.movie?.tmdb_id === id)

  const watchlistMutation = useMutation({
    mutationFn: () =>
      watchlistItem
        ? watchlistService.remove(watchlistItem.id)
        : watchlistService.add(id, 'want_to_watch'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchlist'] })
      toast.success(watchlistItem ? 'Removed from watchlist' : 'Added to watchlist')
    },
    onError: () => toast.error('Failed to update watchlist'),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!movie) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center px-4">
        <p className="text-gray-400">Movie not found.</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-brand-400 hover:underline text-sm">
          Go back
        </button>
      </div>
    )
  }

  const ratingItems: RatingEntry[] = ratingsData?.items ?? []
  const avgScore =
    movie.avg_user_rating ??
    (ratingItems.length > 0
      ? ratingItems.filter(r => r.score).reduce((s, r) => s + (r.score ?? 0), 0) /
        ratingItems.filter(r => r.score).length
      : null)

  return (
    <div className="pb-8">
      {/* Back button */}
      <div className="sticky top-0 z-20 bg-surface/90 backdrop-blur border-b border-surface-border px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-base font-bold text-white truncate">{movie.title}</h1>
      </div>

      {/* Backdrop */}
      {movie.backdrop_url && (
        <div className="relative w-full aspect-video bg-surface-muted overflow-hidden">
          <img
            src={`https://image.tmdb.org/t/p/w1280${movie.backdrop_url}`}
            alt={movie.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/40 to-transparent" />
        </div>
      )}

      {/* Main content */}
      <div className="px-4 py-4">
        <div className="flex gap-4">
          {/* Poster */}
          <div className="flex-shrink-0">
            <img
              src={getPosterUrl(movie.poster_url, 'w185')}
              alt={movie.title}
              className="w-24 rounded-xl shadow-lg"
              onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
            />
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0 space-y-1">
            <h2 className="text-xl font-bold text-white leading-tight">{movie.title}</h2>

            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-400">
              {movie.release_year && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  {movie.release_year}
                </span>
              )}
              {movie.runtime && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                </span>
              )}
              {movie.tmdb_rating && (
                <span className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
                  {movie.tmdb_rating.toFixed(1)}
                </span>
              )}
            </div>

            {/* Genres */}
            {movie.genres && movie.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {movie.genres.map(g => (
                  <span
                    key={g.id}
                    className="px-2 py-0.5 bg-surface-muted border border-surface-border rounded-full text-xs text-gray-400"
                  >
                    {g.name}
                  </span>
                ))}
              </div>
            )}

            {/* Avg user rating */}
            {avgScore !== null && (
              <div className="flex items-center gap-2 pt-1">
                <StarRating value={avgScore} readonly size="sm" />
                <span className="text-xs text-gray-500">
                  {movie.user_rating_count ?? ratingItems.length} ratings
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Overview */}
        {movie.overview && (
          <p className="mt-4 text-sm text-gray-300 leading-relaxed">{movie.overview}</p>
        )}

        {/* Actions */}
        <div className="flex gap-2 mt-5">
          <button
            onClick={() => openRateModal(id)}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-xl transition-colors"
          >
            <Star className="w-4 h-4" />
            Rate
          </button>
          <button
            onClick={() => watchlistMutation.mutate()}
            disabled={watchlistMutation.isPending}
            className={cn(
              'flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-xl transition-colors border',
              watchlistItem
                ? 'bg-brand-600/20 text-brand-400 border-brand-600/40 hover:bg-red-600/20 hover:text-red-400 hover:border-red-600/40'
                : 'bg-surface-muted text-gray-300 border-surface-border hover:bg-surface-card hover:text-white'
            )}
          >
            {watchlistItem ? (
              <BookmarkCheck className="w-4 h-4" />
            ) : (
              <Bookmark className="w-4 h-4" />
            )}
            {watchlistItem ? 'Saved' : 'Watchlist'}
          </button>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-surface-border mx-4 mt-2" />

      {/* Community ratings */}
      <div className="px-4 py-4">
        <h3 className="text-base font-bold text-white mb-3">
          Community Reviews
          {ratingItems.length > 0 && (
            <span className="ml-2 text-gray-500 font-normal text-sm">({ratingItems.length})</span>
          )}
        </h3>

        {ratingItems.length === 0 ? (
          <p className="text-gray-500 text-sm">No reviews yet. Be the first!</p>
        ) : (
          <div className="space-y-4">
            {ratingItems.map(r => (
              <article key={r.id} className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <Avatar src={r.user.avatar_url} username={r.user.username} size="sm" />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-white">
                      {r.user.display_name || r.user.username}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">@{r.user.username}</span>
                  </div>
                  <span className="text-xs text-gray-600">{formatRelativeTime(r.created_at)}</span>
                </div>

                {r.score !== null && (
                  <StarRating value={r.score} readonly size="sm" />
                )}

                {r.review && (
                  <p className="text-sm text-gray-300 leading-relaxed">{r.review}</p>
                )}

                {r.contains_spoiler && (
                  <span className="text-xs text-yellow-500">Contains spoilers</span>
                )}
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
