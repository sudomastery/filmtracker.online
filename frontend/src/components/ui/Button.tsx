import { cn } from '@/utils/helpers'
import { forwardRef } from 'react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, children, className, disabled, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center font-medium rounded-full transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 focus:ring-offset-surface disabled:opacity-50 disabled:cursor-not-allowed'

    const variants = {
      primary:   'bg-brand-600 hover:bg-brand-700 text-white',
      secondary: 'bg-surface-muted hover:bg-surface-border text-white',
      ghost:     'hover:bg-surface-muted text-gray-300 hover:text-white',
      danger:    'bg-red-600 hover:bg-red-700 text-white',
      outline:   'border border-surface-border hover:bg-surface-muted text-gray-300 hover:text-white',
    }

    const sizes = {
      sm:  'px-3 py-1.5 text-sm gap-1.5',
      md:  'px-4 py-2 text-sm gap-2',
      lg:  'px-6 py-2.5 text-base gap-2',
    }

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      >
        {loading && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
