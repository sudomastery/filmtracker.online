import api from './api'
import type { TokenPair } from '@/types/api'
import type { UserMe } from '@/types/user'

export const authService = {
  register: (data: {
    username: string
    email: string
    password: string
    display_name?: string
  }) => api.post<TokenPair>('/auth/register', data),

  login: (username: string, password: string) =>
    api.post<TokenPair>('/auth/login', { username, password }),

  refresh: (refresh_token: string) =>
    api.post<{ access_token: string }>('/auth/refresh', { refresh_token }),

  logout: (refresh_token: string) =>
    api.post('/auth/logout', { refresh_token }),

  getMe: () => api.get<UserMe>('/users/me'),
}
