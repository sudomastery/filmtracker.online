import { getPosterUrl } from '@/utils/helpers'
import type { Movie } from '@/types/movie'
import { StarRating } from '@/components/ui/StarRating'
import { Link } from 'react-router-dom'
import { cn } from '@/utils/helpers'

interface MovieCardProps {
  movie: Movie
  compact?: boolean
  className?: string
}

export function MovieCard({ movie, compact = false, className }: MovieCardProps) {
  const year = movie.release_year ?? (movie.release_date ? movie.release_date.slice(0, 4) : null)

  return (
    <Link
      to={`/movie/${movie.tmdb_id}`}
      className={cn(
        'group block rounded-xl overflow-hidden bg-surface-card border border-surface-border hover:border-brand-600/50 transition-all duration-200 hover:-translate-y-0.5',
        className
      )}
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] overflow-hidden bg-surface-muted">
        <img
          src={getPosterUrl(movie.poster_url)}
          alt={movie.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
          onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
        />
        {movie.avg_user_rating && (
          <div className="absolute bottom-2 left-2 bg-black/70 backdrop-blur-sm rounded-lg px-2 py-0.5 flex items-center gap-1">
            <span className="text-yellow-400 text-xs font-semibold">{movie.avg_user_rating.toFixed(1)}</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-2">
        <h3 className="text-sm font-medium text-white line-clamp-2 leading-tight">{movie.title}</h3>
        {!compact && (
          <p className="text-xs text-gray-500 mt-0.5">{year}</p>
        )}
        {!compact && movie.tmdb_rating && (
          <div className="mt-1 flex items-center gap-1">
            <StarRating value={movie.tmdb_rating} readonly size="sm" />
          </div>
        )}
      </div>
    </Link>
  )
}

/* Horizontal variant used inside feed posts */
export function MovieCardHorizontal({ movie }: { movie: Movie }) {
  const year = movie.release_year ?? (movie.release_date ? movie.release_date.slice(0, 4) : null)

  return (
    <Link
      to={`/movie/${movie.tmdb_id}`}
      className="flex gap-3 p-3 rounded-xl bg-surface-muted hover:bg-surface-border transition-colors"
    >
      <img
        src={getPosterUrl(movie.poster_url, 'w154')}
        alt={movie.title}
        className="w-14 h-20 rounded-lg object-cover flex-shrink-0 bg-surface-border"
        loading="lazy"
        onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
      />
      <div className="min-w-0">
        <h4 className="text-sm font-semibold text-white line-clamp-2">{movie.title}</h4>
        <p className="text-xs text-gray-500 mt-0.5">{year}</p>
        {movie.genres && movie.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {movie.genres.slice(0, 3).map(g => (
              <span key={g.id} className="text-xs px-2 py-0.5 rounded-full bg-surface-border text-gray-400">
                {g.name}
              </span>
            ))}
          </div>
        )}
        {movie.tmdb_rating && (
          <p className="text-xs text-gray-500 mt-1">TMDB {movie.tmdb_rating.toFixed(1)}</p>
        )}
      </div>
    </Link>
  )
}
