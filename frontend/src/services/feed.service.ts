import api from './api'
import type { FeedPage } from '@/types/feed'

export const feedService = {
  getFeed: (cursor?: string, limit = 20) =>
    api.get<FeedPage>('/feed', { params: { cursor, limit } }),

  getGlobalFeed: (cursor?: string, limit = 20) =>
    api.get<FeedPage>('/feed/global', { params: { cursor, limit } }),
}
