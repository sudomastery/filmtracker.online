import type { User } from './user'
import type { Movie } from './movie'

export interface FeedItem {
  id: string
  user: User
  movie: Movie
  score: number | null
  review: string | null
  contains_spoiler: boolean
  watched_on: string | null
  created_at: string
  like_count: number
  liked_by_me: boolean
}

export interface FeedPage {
  items: FeedItem[]
  next_cursor: string | null
  has_more: boolean
}
