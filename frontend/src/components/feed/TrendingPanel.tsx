import { useQuery } from '@tanstack/react-query'
import { movieService } from '@/services/movie.service'
import { Skeleton } from '@/components/ui/Skeleton'
import { TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getPosterUrl } from '@/utils/helpers'
import type { Movie } from '@/types/movie'

function TrendingItem({ movie }: { movie: Movie }) {
  return (
    <Link
      to={`/movie/${movie.tmdb_id}`}
      className="block rounded-xl overflow-hidden bg-surface-card border border-surface-border hover:border-brand-600/50 transition-all duration-200 flex-shrink-0"
    >
      <div className="aspect-[2/3] relative">
        <img
          src={getPosterUrl(movie.poster_url)}
          alt={movie.title}
          className="w-full h-full object-cover"
          loading="lazy"
          onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
        />
      </div>
      <div className="p-1.5">
        <p className="text-xs text-white line-clamp-1 font-medium">{movie.title}</p>
        {movie.release_year && (
          <p className="text-xs text-gray-500">{movie.release_year}</p>
        )}
      </div>
    </Link>
  )
}

export function TrendingPanel() {
  const { data: trending, isLoading } = useQuery({
    queryKey: ['trending'],
    queryFn: () => movieService.getTrending().then(r => r.data),
    staleTime: 1000 * 60 * 60,
  })

  const movies = trending?.slice(0, 10) ?? []
  // Interleave: left column gets even indices (0,2,4,6,8), right gets odd (1,3,5,7,9)
  const leftMovies  = movies.filter((_, i) => i % 2 === 0)
  const rightMovies = movies.filter((_, i) => i % 2 === 1)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp className="w-4 h-4 text-brand-400" />
        <h3 className="font-semibold text-white text-sm">Trending This Week</h3>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-2">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="w-full aspect-[2/3] rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="flex gap-2 overflow-hidden h-[480px]">
          {/* Left column — scrolls up */}
          <div className="flex-1 flex flex-col gap-2 animate-scroll-up hover:[animation-play-state:paused]">
            {[...leftMovies, ...leftMovies].map((movie, i) => (
              <TrendingItem key={`l-${i}`} movie={movie} />
            ))}
          </div>
          {/* Right column — scrolls down */}
          <div className="flex-1 flex flex-col gap-2 animate-scroll-down hover:[animation-play-state:paused]">
            {[...rightMovies, ...rightMovies].map((movie, i) => (
              <TrendingItem key={`r-${i}`} movie={movie} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
