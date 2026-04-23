export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface ApiError {
  detail: string | { msg: string; type: string }[]
}

export interface Notification {
  id: string
  type: string
  read: boolean
  created_at: string
  entity_id: string | null
  actor: {
    id: string
    username: string
    display_name: string | null
    avatar_url: string | null
  }
}

export interface ImportStatus {
  job_id: string
  status: 'pending' | 'processing' | 'done' | 'failed'
  total: number
  processed: number
  matched: number
  unmatched: number
}

export interface ImportMovieResult {
  line: string
  matched: boolean
  tmdb_id?: number
  title?: string
  poster_url?: string
  release_year?: number
  confidence?: number
}
