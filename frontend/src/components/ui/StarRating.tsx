import { cn } from '@/utils/helpers'
import { Star } from 'lucide-react'
import { useState } from 'react'

interface StarRatingProps {
  value?: number | null
  onChange?: (score: number) => void
  readonly?: boolean
  size?: 'sm' | 'md' | 'lg'
  max?: number
}

export function StarRating({
  value,
  onChange,
  readonly = false,
  size = 'md',
  max = 10,
}: StarRatingProps) {
  const [hovered, setHovered] = useState<number | null>(null)
  const stars = max / 2 // Show half the number as stars (so 10/2 = 5 stars but each = 2 pts)
  const displayStars = 5

  const sizeMap = { sm: 'w-3.5 h-3.5', md: 'w-5 h-5', lg: 'w-6 h-6' }
  const iconSize = sizeMap[size]

  const normalizedValue = value !== null && value !== undefined ? value / 2 : null
  const displayValue = hovered !== null ? hovered : normalizedValue

  return (
    <div
      className={cn('flex gap-0.5', readonly && 'pointer-events-none')}
      onMouseLeave={() => !readonly && setHovered(null)}
    >
      {Array.from({ length: displayStars }, (_, i) => {
        const starVal = i + 1
        const filled = displayValue !== null && displayValue >= starVal
        const halfFilled = displayValue !== null && displayValue >= starVal - 0.5 && displayValue < starVal

        return (
          <button
            key={i}
            type="button"
            onClick={() => !readonly && onChange?.(starVal * 2)}
            onMouseEnter={() => !readonly && setHovered(starVal)}
            className={cn(
              'transition-colors',
              !readonly && 'cursor-pointer hover:scale-110',
              filled || halfFilled ? 'text-yellow-400' : 'text-gray-600'
            )}
          >
            <Star
              className={cn(iconSize, (filled || halfFilled) && 'fill-yellow-400')}
            />
          </button>
        )
      })}
      {value !== null && value !== undefined && (
        <span className={cn('ml-1 font-semibold text-yellow-400', size === 'sm' ? 'text-xs' : 'text-sm')}>
          {value.toFixed(1)}
        </span>
      )}
    </div>
  )
}
