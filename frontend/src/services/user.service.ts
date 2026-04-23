import api from './api'
import type { UserProfile } from '@/types/user'

export const userService = {
  getProfile: (username: string) => api.get<UserProfile>(`/users/${username}`),

  updateMe: (data: { display_name?: string; bio?: string; avatar_url?: string }) =>
    api.patch('/users/me', data),

  follow: (username: string) => api.post(`/users/${username}/follow`),

  unfollow: (username: string) => api.delete(`/users/${username}/follow`),

  getFollowers: (username: string) => api.get<UserProfile[]>(`/users/${username}/followers`),

  getFollowing: (username: string) => api.get<UserProfile[]>(`/users/${username}/following`),

  getUserRatings: (username: string) => api.get(`/users/${username}/ratings`),
}

export const onboardingService = {
  saveGenres: (genre_ids: number[], genre_names: string[]) =>
    api.post('/onboarding/genres', { genre_ids, genre_names }),

  getSuggestions: () => api.get('/onboarding/suggestions'),

  complete: () => api.post('/onboarding/complete'),
}

export const notificationService = {
  getAll: () => api.get('/notifications'),

  markAllRead: () => api.patch('/notifications/read-all'),

  markRead: (id: string) => api.patch(`/notifications/${id}/read`),
}

export const importService = {
  uploadTxt: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<{ job_id: string }>('/import/txt', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getStatus: (jobId: string) => api.get(`/import/${jobId}/status`),

  getResults: (jobId: string) => api.get(`/import/${jobId}/results`),
}
