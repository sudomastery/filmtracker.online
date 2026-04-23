import { useEffect, useRef, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { feedService } from '@/services/feed.service'
import { FeedPost } from '@/components/feed/FeedPost'
import { FeedSkeleton } from '@/components/ui/Skeleton'
import { useUIStore } from '@/store/uiStore'
import { cn } from '@/utils/helpers'
import type { FeedPage } from '@/types/feed'

type Tab = 'mylist' | 'following' | 'community'

const TABS: { id: Tab; label: string }[] = [
  { id: 'mylist',    label: 'My List' },
  { id: 'following', label: 'Following' },
  { id: 'community', label: 'Community' },
]

const EMPTY_MESSAGES: Record<Tab, { heading: string; sub: string }> = {
  mylist: {
    heading: "You haven't rated anything yet",
    sub: 'Rate your first movie to see it here.',
  },
  following: {
    heading: 'Your following feed is empty',
    sub: 'Follow friends or rate movies to see activity here.',
  },
  community: {
    heading: 'No community posts yet',
    sub: 'Be the first to rate a movie!',
  },
}

export default function Home() {
  const { openRateModal } = useUIStore()
  const [tab, setTab] = useState<Tab>('following')
  const loadMoreRef = useRef<HTMLDivElement>(null)

  const myListQuery = useInfiniteQuery<FeedPage>({
    queryKey: ['feed', 'me'],
    queryFn: ({ pageParam }) =>
      feedService.getMyFeed(pageParam as string | undefined).then(r => r.data),
    getNextPageParam: page => (page.has_more ? page.next_cursor ?? undefined : undefined),
    initialPageParam: undefined,
    enabled: tab === 'mylist',
  })

  const followingQuery = useInfiniteQuery<FeedPage>({
    queryKey: ['feed', 'following'],
    queryFn: ({ pageParam }) =>
      feedService.getFeed(pageParam as string | undefined).then(r => r.data),
    getNextPageParam: page => (page.has_more ? page.next_cursor ?? undefined : undefined),
    initialPageParam: undefined,
    enabled: tab === 'following',
  })

  const communityQuery = useInfiniteQuery<FeedPage>({
    queryKey: ['feed', 'global'],
    queryFn: ({ pageParam }) =>
      feedService.getGlobalFeed(pageParam as string | undefined).then(r => r.data),
    getNextPageParam: page => (page.has_more ? page.next_cursor ?? undefined : undefined),
    initialPageParam: undefined,
    enabled: tab === 'community',
  })

  const activeQuery =
    tab === 'mylist'    ? myListQuery :
    tab === 'following' ? followingQuery :
    communityQuery

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, isError } = activeQuery

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    const el = loadMoreRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage()
        }
      },
      { threshold: 0.1 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const allItems = data?.pages.flatMap(p => p.items) ?? []

  return (
    <div>
      {/* Sticky header with tabs */}
      <div className="sticky top-0 z-20 bg-surface/90 backdrop-blur border-b border-surface-border">
        <div className="px-4 py-3">
          <h1 className="text-lg font-bold text-white">Home</h1>
        </div>
        <div className="flex">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                'flex-1 py-2.5 text-sm font-medium border-b-2 transition-colors',
                tab === t.id
                  ? 'text-white border-brand-500'
                  : 'text-gray-500 border-transparent hover:text-gray-300 hover:border-gray-600'
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Compose CTA */}
      <div className="px-4 py-3 border-b border-surface-border flex items-center gap-3">
        <div className="flex-1">
          <button
            onClick={() => openRateModal(0)}
            className="w-full text-left text-gray-500 hover:text-gray-300 bg-surface-muted hover:bg-surface-card border border-surface-border rounded-xl px-4 py-2.5 text-sm transition-colors"
          >
            What have you been watching?
          </button>
        </div>
        <button
          onClick={() => openRateModal(0)}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-xl transition-colors flex-shrink-0"
        >
          Rate
        </button>
      </div>

      {/* Feed content */}
      {isLoading && <FeedSkeleton count={5} />}

      {isError && (
        <div className="flex flex-col items-center justify-center py-16 text-center px-4">
          <p className="text-gray-400 mb-2">Failed to load your feed.</p>
          <p className="text-gray-600 text-sm">Try switching tabs or refreshing.</p>
        </div>
      )}

      {!isLoading && allItems.length === 0 && !isError && (
        <div className="flex flex-col items-center justify-center py-16 text-center px-4">
          <p className="text-xl mb-2">🎬</p>
          <p className="text-gray-300 font-semibold mb-1">{EMPTY_MESSAGES[tab].heading}</p>
          <p className="text-gray-500 text-sm mb-4">{EMPTY_MESSAGES[tab].sub}</p>
          <button
            onClick={() => openRateModal(0)}
            className="px-5 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-xl transition-colors"
          >
            Rate your first movie
          </button>
        </div>
      )}

      {allItems.map(item => (
        <FeedPost key={item.id} item={item} />
      ))}

      {/* Load more sentinel */}
      <div ref={loadMoreRef} className="py-4 flex justify-center">
        {isFetchingNextPage && (
          <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        )}
        {!hasNextPage && allItems.length > 0 && (
          <p className="text-gray-600 text-xs">You're all caught up</p>
        )}
      </div>
    </div>
  )
}
