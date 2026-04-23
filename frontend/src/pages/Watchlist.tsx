import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Bookmark, Trash2, ChevronDown } from 'lucide-react'
import { watchlistService } from '@/services/movie.service'
import { getPosterUrl, cn } from '@/utils/helpers'
import type { WatchlistItem, WatchlistStatus } from '@/types/movie'
import toast from 'react-hot-toast'

const TABS: { key: WatchlistStatus | 'all'; label: string }[] = [
  { key: 'all',            label: 'All' },
  { key: 'want_to_watch',  label: 'Want to Watch' },
  { key: 'watching',       label: 'Watching' },
  { key: 'watched',        label: 'Watched' },
]

const STATUS_LABELS: Record<WatchlistStatus, string> = {
  want_to_watch: 'Want to Watch',
  watching: 'Watching',
  watched: 'Watched',
}

export default function WatchlistPage() {
  const [activeTab, setActiveTab] = useState<WatchlistStatus | 'all'>('all')
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: watchlist, isLoading } = useQuery<WatchlistItem[]>({
    queryKey: ['watchlist'],
    queryFn: () => watchlistService.getWatchlist().then(r => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: WatchlistStatus }) =>
      watchlistService.updateStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
    onError: () => toast.error('Failed to update status'),
  })

  const removeMutation = useMutation({
    mutationFn: (id: string) => watchlistService.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchlist'] })
      toast.success('Removed from watchlist')
    },
    onError: () => toast.error('Failed to remove'),
  })

  const filtered = (watchlist ?? []).filter(
    item => activeTab === 'all' || item.status === activeTab
  )

  return (
    <div>
      {/* Header */}
      <div className="sticky top-0 z-20 bg-surface/90 backdrop-blur border-b border-surface-border px-4 py-3">
        <h1 className="text-lg font-bold text-white">Watchlist</h1>
      </div>

      {/* Tabs */}
      <div className="flex overflow-x-auto scrollbar-none border-b border-surface-border px-2">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-shrink-0 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
              activeTab === tab.key
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {tab.label}
            {watchlist && (
              <span className="ml-1.5 text-xs text-gray-600">
                ({tab.key === 'all'
                  ? watchlist.length
                  : watchlist.filter(w => w.status === tab.key).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center px-4">
          <Bookmark className="w-10 h-10 text-gray-700 mb-3" />
          <p className="text-gray-300 font-semibold mb-1">Nothing here yet</p>
          <p className="text-gray-500 text-sm">
            Add movies to your watchlist from their detail pages.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-surface-border">
          {filtered.map(item => (
            <div key={item.id} className="flex gap-3 px-4 py-3 hover:bg-surface-card/40 transition-colors">
              {/* Poster */}
              <button
                onClick={() => navigate(`/movie/${item.movie.tmdb_id}`)}
                className="flex-shrink-0"
              >
                <img
                  src={getPosterUrl(item.movie.poster_url, 'w92')}
                  alt={item.movie.title}
                  className="w-12 h-[72px] rounded-lg object-cover bg-surface-muted"
                  onError={e => { (e.target as HTMLImageElement).src = '/placeholder-poster.svg' }}
                />
              </button>

              {/* Info */}
              <div className="flex-1 min-w-0 py-0.5">
                <button
                  onClick={() => navigate(`/movie/${item.movie.tmdb_id}`)}
                  className="text-sm font-semibold text-white hover:underline text-left"
                >
                  {item.movie.title}
                </button>
                {item.movie.release_year && (
                  <p className="text-xs text-gray-500 mt-0.5">{item.movie.release_year}</p>
                )}

                {/* Status dropdown */}
                <div className="relative mt-2 inline-block">
                  <select
                    value={item.status}
                    onChange={e =>
                      updateMutation.mutate({
                        id: item.id,
                        status: e.target.value as WatchlistStatus,
                      })
                    }
                    className="appearance-none pl-2.5 pr-6 py-1 rounded-lg bg-surface-muted border border-surface-border text-xs text-gray-300 focus:outline-none focus:border-brand-500 cursor-pointer"
                  >
                    {Object.entries(STATUS_LABELS).map(([val, label]) => (
                      <option key={val} value={val}>
                        {label}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-500" />
                </div>
              </div>

              {/* Remove */}
              <button
                onClick={() => removeMutation.mutate(item.id)}
                disabled={removeMutation.isPending}
                className="self-center flex-shrink-0 p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-400/10 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
