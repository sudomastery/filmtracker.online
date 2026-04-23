import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, AlertTriangle } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { FeedItem } from '@/types/feed'
import { Avatar } from '@/components/ui/Avatar'
import { MovieCardHorizontal } from '@/components/movie/MovieCard'
import { StarRating } from '@/components/ui/StarRating'
import { formatRelativeTime } from '@/utils/helpers'
import { cn } from '@/utils/helpers'
import { ratingService } from '@/services/movie.service'

interface FeedPostProps {
  item: FeedItem
}

export function FeedPost({ item }: FeedPostProps) {
  const [expanded, setExpanded] = useState(false)
  const qc = useQueryClient()
  const { user, movie, score, review, contains_spoiler, watched_on, created_at } = item
  const longReview = review && review.length > 240

  // Optimistic like toggle
  const [optimisticLiked, setOptimisticLiked] = useState<boolean | null>(null)
  const [optimisticCount, setOptimisticCount] = useState<number | null>(null)

  const liked = optimisticLiked !== null ? optimisticLiked : item.liked_by_me
  const likeCount = optimisticCount !== null ? optimisticCount : item.like_count

  const likeMutation = useMutation({
    mutationFn: () => ratingService.like(item.id).then(r => r.data),
    onMutate: () => {
      // Optimistic update
      setOptimisticLiked(!liked)
      setOptimisticCount(liked ? likeCount - 1 : likeCount + 1)
    },
    onSuccess: (data) => {
      setOptimisticLiked(data.liked)
      setOptimisticCount(data.like_count)
      // Invalidate feed to sync server state in background
      qc.invalidateQueries({ queryKey: ['feed'] })
    },
    onError: () => {
      // Revert on error
      setOptimisticLiked(null)
      setOptimisticCount(null)
    },
  })

  return (
    <article className="px-4 py-4 border-b border-surface-border hover:bg-surface-card/40 transition-colors">
      <div className="flex gap-3">
        {/* Avatar */}
        <Link to={`/profile/${user.username}`} className="flex-shrink-0">
          <Avatar src={user.avatar_url} username={user.username} size="md" />
        </Link>

        <div className="flex-1 min-w-0 space-y-2">
          {/* User + time */}
          <div className="flex items-center gap-2 flex-wrap">
            <Link to={`/profile/${user.username}`} className="font-semibold text-white text-sm hover:underline">
              {user.display_name || user.username}
            </Link>
            <Link to={`/profile/${user.username}`} className="text-gray-500 text-sm hover:underline">
              @{user.username}
            </Link>
            <span className="text-gray-600 text-xs">·</span>
            <span className="text-gray-500 text-xs">{formatRelativeTime(created_at)}</span>
          </div>

          {/* Score */}
          {score !== null && score !== undefined && (
            <div className="flex items-center gap-2">
              <StarRating value={score} readonly size="sm" />
              <span className="text-xs text-gray-500">
                {watched_on && `Watched ${watched_on}`}
              </span>
            </div>
          )}

          {/* Movie card */}
          <MovieCardHorizontal movie={movie} />

          {/* Review */}
          {review && (
            <div className="mt-1">
              {contains_spoiler && (
                <div className="flex items-center gap-1.5 text-yellow-500 text-xs mb-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Contains spoilers</span>
                </div>
              )}
              <p
                className={cn(
                  'text-sm text-gray-300 leading-relaxed whitespace-pre-wrap',
                  !expanded && longReview && 'line-clamp-3'
                )}
              >
                {review}
              </p>
              {longReview && (
                <button
                  onClick={() => setExpanded(v => !v)}
                  className="text-brand-400 text-xs mt-0.5 hover:underline"
                >
                  {expanded ? 'Show less' : 'Read more'}
                </button>
              )}
            </div>
          )}

          {/* Action row */}
          <div className="flex items-center gap-5 pt-1 -ml-1">
            <button
              onClick={() => likeMutation.mutate()}
              disabled={likeMutation.isPending}
              className={cn(
                'flex items-center gap-1.5 text-sm transition-colors group',
                liked ? 'text-red-500' : 'text-gray-500 hover:text-red-400'
              )}
              aria-label={liked ? 'Unlike' : 'Like'}
            >
              <Heart
                className={cn(
                  'w-4 h-4 transition-transform group-active:scale-125',
                  liked && 'fill-red-500'
                )}
              />
              {likeCount > 0 && (
                <span className="text-xs tabular-nums">{likeCount}</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </article>
  )
}
