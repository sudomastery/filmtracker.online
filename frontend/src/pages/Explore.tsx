import { useState, useEffect, useRef } from 'react'
import { useQuery, useInfiniteQuery } from '@tanstack/react-query'
import { movieService } from '@/services/movie.service'
import { feedService } from '@/services/feed.service'
import { MovieCard } from '@/components/movie/MovieCard'
import { FeedPost } from '@/components/feed/FeedPost'
import { FeedSkeleton, MovieCardSkeleton } from '@/components/ui/Skeleton'
import type { Movie } from '@/types/movie'
import type { FeedPage } from '@/types/feed'

type Tab = 'trending' | 'global'

export default function Explore() {
  const [tab, setTab] = useState<Tab>('trending')
  const [selectedGenre, setSelectedGenre] = useState<number | null>(null)
  const loadMoreRef = useRef<HTMLDivElement>(null)

  const { data: trending, isLoading: trendingLoading } = useQuery<Movie[]>({
    queryKey: ['trending'],
    queryFn: () => movieService.getTrending().then(r => r.data),
    staleTime: 5 * 60 * 1000,
  })

  const { data: genres } = useQuery<{ id: number; name: string }[]>({
    queryKey: ['genres'],
    queryFn: () => movieService.getGenres().then(r => r.data),
    staleTime: Infinity,
  })

  const {
    data: globalData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: globalLoading,
  } = useInfiniteQuery<FeedPage>({
    queryKey: ['global-feed'],
    queryFn: ({ pageParam }) =>
      feedService.getGlobalFeed(pageParam as string | undefined).then(r => r.data),
    getNextPageParam: page => (page.has_more ? page.next_cursor ?? undefined : undefined),
    initialPageParam: undefined,
    enabled: tab === 'global',
  })

  // Infinite scroll sentinel
  useEffect(() => {
    const el = loadMoreRef.current
    if (!el || tab !== 'global') return
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage()
        }
      },
      { threshold: 0.1 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, tab])

  const filteredTrending = selectedGenre
    ? (trending ?? []).filter(m => m.genres?.some(g => g.id === selectedGenre))
    : (trending ?? [])

  const globalItems = globalData?.pages.flatMap(p => p.items) ?? []

  return (
    <div>
      {/* Header */}
      <div className="sticky top-0 z-20 bg-surface/90 backdrop-blur border-b border-surface-border px-4 py-3">
        <h1 className="text-lg font-bold text-white">Explore</h1>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-surface-border">
        {(['trending', 'global'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-3 text-sm font-medium transition-colors border-b-2 ${
              tab === t
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {t === 'trending' ? 'Trending' : 'Global Feed'}
          </button>
        ))}
      </div>

      {/* Trending tab */}
      {tab === 'trending' && (
        <>
          {/* Genre chips */}
          {genres && genres.length > 0 && (
            <div className="px-4 py-3 flex gap-2 overflow-x-auto scrollbar-none border-b border-surface-border">
              <button
                onClick={() => setSelectedGenre(null)}
                className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  selectedGenre === null
                    ? 'bg-brand-600 text-white'
                    : 'bg-surface-muted text-gray-400 hover:text-white'
                }`}
              >
                All
              </button>
              {genres.map(g => (
                <button
                  key={g.id}
                  onClick={() => setSelectedGenre(prev => prev === g.id ? null : g.id)}
                  className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    selectedGenre === g.id
                      ? 'bg-brand-600 text-white'
                      : 'bg-surface-muted text-gray-400 hover:text-white'
                  }`}
                >
                  {g.name}
                </button>
              ))}
            </div>
          )}

          {/* Trending grid */}
          {trendingLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <MovieCardSkeleton key={i} />
              ))}
            </div>
          ) : filteredTrending.length === 0 ? (
            <div className="flex items-center justify-center py-16 text-gray-500 text-sm">
              No movies found for this genre.
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4">
              {filteredTrending.map(movie => (
                <MovieCard
                  key={movie.tmdb_id}
                  movie={movie}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Global feed tab */}
      {tab === 'global' && (
        <>
          {globalLoading && <FeedSkeleton count={5} />}

          {globalItems.map(item => (
            <FeedPost key={item.id} item={item} />
          ))}

          <div ref={loadMoreRef} className="py-4 flex justify-center">
            {isFetchingNextPage && (
              <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
            )}
            {!hasNextPage && globalItems.length > 0 && (
              <p className="text-gray-600 text-xs">End of global feed</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
