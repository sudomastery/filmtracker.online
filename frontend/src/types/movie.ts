export interface Genre {
  id: number
  name: string
}

export interface Movie {
  id: string
  tmdb_id: number
  title: string
  release_year: number | null
  release_date: string | null
  poster_url: string | null
  backdrop_url: string | null
  overview: string | null
  genres: Genre[] | null
  runtime: number | null
  tmdb_rating: number | null
  avg_user_rating?: number | null
  user_rating_count?: number
}

export interface Rating {
  id: string
  user_id: string
  movie_id: string
  score: number | null
  review: string | null
  contains_spoiler: boolean
  watched_on: string | null
  created_at: string
  updated_at: string
}

export interface WatchlistItem {
  id: string
  status: 'want_to_watch' | 'watching' | 'watched'
  added_at: string
  movie: Movie
}

export type WatchlistStatus = 'want_to_watch' | 'watching' | 'watched'
