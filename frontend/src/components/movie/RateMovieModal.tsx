import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Search, Star } from 'lucide-react'
import { useUIStore } from '@/store/uiStore'
import { movieService, ratingService } from '@/services/movie.service'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { StarRating } from '@/components/ui/StarRating'
import { getPosterUrl } from '@/utils/helpers'
import type { Movie } from '@/types/movie'
import toast from 'react-hot-toast'
import { useDebounce } from '@/hooks/useDebounce'

export function RateMovieModal() {
  const { closeModal, modalMovieTmdbId } = useUIStore()
  const qc = useQueryClient()

  const [query, setQuery] = useState('')
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null)
  const [score, setScore] = useState<number>(0)
  const [review, setReview] = useState('')
  const [spoiler, setSpoiler] = useState(false)
  const [watchedOn, setWatchedOn] = useState('')
  const debouncedQuery = useDebounce(query, 400)

  // If a specific movie was requested, load it
  const { data: preloadedMovie } = useQuery({
    queryKey: ['modal-movie', modalMovieTmdbId],
    queryFn: () => movieService.getMovie(modalMovieTmdbId!).then(r => r.data),
    enabled: !!modalMovieTmdbId && modalMovieTmdbId > 0,
  })
  useEffect(() => {
    if (preloadedMovie) setSelectedMovie(preloadedMovie)
  }, [preloadedMovie])

  const { data: searchResults, isFetching } = useQuery({
    queryKey: ['modal-search', debouncedQuery],
    queryFn: () => movieService.search(debouncedQuery).then(r => r.data.results),
    enabled: debouncedQuery.length > 1 && !selectedMovie,
    placeholderData: [],
  })

  const mutation = useMutation({
    mutationFn: () =>
      ratingService.createOrUpdate({
        tmdb_id: selectedMovie!.tmdb_id,
        score: score || null,
        review: review || null,
        contains_spoiler: spoiler,
        watched_on: watchedOn || null,
      }),
    onSuccess: () => {
      toast.success('Rating saved!')
      qc.invalidateQueries({ queryKey: ['feed'] })
      qc.invalidateQueries({ queryKey: ['movie', selectedMovie?.tmdb_id] })
      qc.invalidateQueries({ queryKey: ['my-ratings'] })
      closeModal()
    },
    onError: () => toast.error('Failed to save rating'),
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-surface-card border border-surface-border rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-surface-border">
          <h2 className="text-lg font-bold text-white">
            {selectedMovie ? 'Rate Movie' : 'Search a Movie'}
          </h2>
          <button onClick={closeModal} className="text-gray-500 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Movie picker */}
          {!selectedMovie ? (
            <>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  autoFocus
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Search for a movie..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface-muted border border-surface-border text-white placeholder-gray-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              {isFetching && (
                <div className="flex justify-center py-4">
                  <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}

              {searchResults && searchResults.length > 0 && (
                <ul className="space-y-2 max-h-72 overflow-y-auto">
                  {searchResults.map((m: Movie) => (
                    <li key={m.tmdb_id}>
                      <button
                        onClick={() => setSelectedMovie(m)}
                        className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-surface-muted transition-colors text-left"
                      >
                        <img
                          src={getPosterUrl(m.poster_url, 'w92')}
                          alt={m.title}
                          className="w-10 h-14 rounded-lg object-cover bg-surface-border flex-shrink-0"
                          onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
                        />
                        <div>
                          <p className="text-sm font-medium text-white">{m.title}</p>
                          <p className="text-xs text-gray-500">{m.release_year}</p>
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <>
              {/* Selected movie header */}
              <div className="flex gap-3 p-3 bg-surface-muted rounded-xl">
                <img
                  src={getPosterUrl(selectedMovie.poster_url, 'w92')}
                  alt={selectedMovie.title}
                  className="w-12 h-16 rounded-lg object-cover flex-shrink-0"
                  onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
                />
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white">{selectedMovie.title}</p>
                  <p className="text-sm text-gray-500">{selectedMovie.release_year}</p>
                </div>
                <button
                  onClick={() => setSelectedMovie(null)}
                  className="text-gray-500 hover:text-white self-start"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Score */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Your Score</label>
                <div className="flex items-center gap-3">
                  <StarRating value={score || null} onChange={setScore} size="lg" />
                  {score > 0 && (
                    <button onClick={() => setScore(0)} className="text-xs text-gray-500 hover:text-white">
                      clear
                    </button>
                  )}
                </div>
              </div>

              {/* Review */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Review <span className="text-gray-500">(optional)</span></label>
                <textarea
                  value={review}
                  onChange={e => setReview(e.target.value)}
                  rows={4}
                  maxLength={2000}
                  placeholder="What did you think?"
                  className="w-full px-4 py-2.5 rounded-xl bg-surface-muted border border-surface-border text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 resize-none text-sm"
                />
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={spoiler}
                      onChange={e => setSpoiler(e.target.checked)}
                      className="rounded accent-brand-600"
                    />
                    <span className="text-xs text-gray-400">Contains spoilers</span>
                  </label>
                  <span className="text-xs text-gray-500">{review.length}/2000</span>
                </div>
              </div>

              {/* Watched on */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Watched on <span className="text-gray-500">(optional)</span></label>
                <input
                  type="date"
                  value={watchedOn}
                  onChange={e => setWatchedOn(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-surface-muted border border-surface-border text-white focus:outline-none focus:border-brand-500 text-sm [color-scheme:dark]"
                />
              </div>

              <Button
                className="w-full"
                loading={mutation.isPending}
                disabled={!selectedMovie}
                onClick={() => mutation.mutate()}
              >
                Save Rating
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
