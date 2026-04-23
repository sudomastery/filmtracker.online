import { useQuery } from '@tanstack/react-query'
import { movieService } from '@/services/movie.service'
import { MovieCard } from '@/components/movie/MovieCard'
import { Skeleton } from '@/components/ui/Skeleton'
import { TrendingUp } from 'lucide-react'

export function TrendingPanel() {
  const { data: trending, isLoading } = useQuery({
    queryKey: ['trending'],
    queryFn: () => movieService.getTrending().then(r => r.data),
    staleTime: 1000 * 60 * 60,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp className="w-4 h-4 text-brand-400" />
        <h3 className="font-semibold text-white text-sm">Trending This Week</h3>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="w-full aspect-[2/3] rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {trending?.slice(0, 10).map(movie => (
            <MovieCard key={movie.tmdb_id} movie={movie} compact />
          ))}
        </div>
      )}
    </div>
  )
}
