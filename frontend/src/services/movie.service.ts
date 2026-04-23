import api from './api'
import type { Movie, WatchlistItem, WatchlistStatus } from '@/types/movie'

export const movieService = {
  search: (q: string, page = 1) =>
    api.get<{ results: Movie[]; total_results: number; total_pages: number }>('/movies/search', {
      params: { q, page },
    }),

  getMovie: (tmdbId: number) => api.get<Movie>(`/movies/${tmdbId}`),

  getTrending: () => api.get<Movie[]>('/movies/trending'),

  getGenres: () => api.get<{ id: number; name: string }[]>('/movies/genres'),

  getMovieRatings: (tmdbId: number, page = 1) =>
    api.get(`/movies/${tmdbId}/ratings`, { params: { page } }),
}

export const ratingService = {
  createOrUpdate: (data: {
    tmdb_id: number
    score?: number | null
    review?: string | null
    contains_spoiler?: boolean
    watched_on?: string | null
  }) => api.post('/ratings', data),

  delete: (ratingId: string) => api.delete(`/ratings/${ratingId}`),

  getMyRatings: () => api.get('/ratings/me'),

  like: (ratingId: string) =>
    api.post<{ liked: boolean; like_count: number }>(`/ratings/${ratingId}/like`),
}

export const watchlistService = {
  getWatchlist: () => api.get<WatchlistItem[]>('/watchlist'),

  add: (tmdb_id: number, status: WatchlistStatus = 'want_to_watch') =>
    api.post('/watchlist', { tmdb_id, status }),

  updateStatus: (id: string, status: WatchlistStatus) =>
    api.patch(`/watchlist/${id}`, { status }),

  remove: (id: string) => api.delete(`/watchlist/${id}`),
}
