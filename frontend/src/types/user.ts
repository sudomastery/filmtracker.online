export interface User {
  id: string
  username: string
  display_name: string | null
  avatar_url: string | null
  bio: string | null
  created_at: string
}

export interface UserMe extends User {
  email: string
  onboarding_complete: boolean
  follower_count: number
  following_count: number
}

export interface UserProfile extends User {
  follower_count: number
  following_count: number
  rating_count: number
  is_following: boolean
}
