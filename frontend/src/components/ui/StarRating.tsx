import { cn } from '@/utils/helpers'
import { Star } from 'lucide-react'
import { useState } from 'react'

interface StarRatingProps {
  value?: number | null
  onChange?: (score: number) => void
  readonly?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const STARS = 10

export function StarRating({
  value,
  onChange,
  readonly = false,
  size = 'md',
}: StarRatingProps) {
  const [hovered, setHovered] = useState<number | null>(null)

  const sizeMap = { sm: 'w-3.5 h-3.5', md: 'w-5 h-5', lg: 'w-6 h-6' }
  const iconSize = sizeMap[size]

  const displayValue = hovered !== null ? hovered : (value ?? null)

  const getStarValue = (
    e: React.MouseEvent<HTMLButtonElement>,
    starIndex: number
  ) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    return x < rect.width / 2 ? starIndex - 0.5 : starIndex
  }

  return (
    <div
      className={cn('flex items-center gap-0.5', readonly && 'pointer-events-none')}
      onMouseLeave={() => !readonly && setHovered(null)}
    >
      {Array.from({ length: STARS }, (_, i) => {
        const starIndex = i + 1
        const filled = displayValue !== null && displayValue >= starIndex
        const halfFilled =
          displayValue !== null &&
          displayValue >= starIndex - 0.5 &&
          displayValue < starIndex

        return (
          <button
            key={i}
            type="button"
            onMouseMove={e => !readonly && setHovered(getStarValue(e, starIndex))}
            onClick={e => !readonly && onChange?.(getStarValue(e, starIndex))}
            className={cn(
              'relative transition-transform',
              !readonly && 'cursor-pointer hover:scale-110'
            )}
          >
            {/* Base: empty star */}
            <Star className={cn(iconSize, 'text-gray-600')} />
            {/* Overlay: filled star, clipped to full or half width */}
            {(filled || halfFilled) && (
              <div
                className="absolute inset-0 overflow-hidden"
                style={{ width: halfFilled ? '50%' : '100%' }}
              >
                <Star className={cn(iconSize, 'text-yellow-400 fill-yellow-400')} />
              </div>
            )}
          </button>
        )
      })}
      {displayValue !== null && displayValue > 0 && (
        <span
          className={cn(
            'ml-1 font-semibold text-yellow-400',
            size === 'sm' ? 'text-xs' : 'text-sm'
          )}
        >
          {displayValue.toFixed(1)}
        </span>
      )}
    </div>
  )
}
