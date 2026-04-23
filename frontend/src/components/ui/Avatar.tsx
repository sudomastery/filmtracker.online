import { cn } from '@/utils/helpers'

interface AvatarProps {
  src?: string | null
  username: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

const sizeMap = {
  sm:  'w-8 h-8 text-xs',
  md:  'w-10 h-10 text-sm',
  lg:  'w-12 h-12 text-base',
  xl:  'w-16 h-16 text-xl',
}

export function Avatar({ src, username, size = 'md', className }: AvatarProps) {
  const fallbackUrl = `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(username)}&backgroundColor=a928d8&textColor=ffffff`

  return (
    <img
      src={src || fallbackUrl}
      alt={username}
      className={cn(
        'rounded-full object-cover flex-shrink-0 bg-surface-muted',
        sizeMap[size],
        className
      )}
      onError={(e) => {
        ;(e.target as HTMLImageElement).src = fallbackUrl
      }}
    />
  )
}
