import { cn } from '@/utils/helpers'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn('animate-pulse rounded-lg bg-surface-muted', className)} />
  )
}

export function FeedSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="divide-y divide-surface-border">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="p-4 flex gap-3">
          <Skeleton className="w-10 h-10 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-32" />
            <div className="flex gap-3">
              <Skeleton className="w-16 h-24 rounded-lg flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function MovieCardSkeleton() {
  return (
    <div className="space-y-2">
      <Skeleton className="w-full aspect-[2/3] rounded-xl" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  )
}
