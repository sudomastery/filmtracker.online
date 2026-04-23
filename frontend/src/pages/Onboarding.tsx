import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Film, Check } from 'lucide-react'
import { useOnboardingStore } from '@/store/onboardingStore'
import { useAuthStore } from '@/store/authStore'
import { movieService } from '@/services/movie.service'
import { onboardingService, userService } from '@/services/user.service'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'
import { FollowButton } from '@/components/profile/FollowButton'
import { cn } from '@/utils/helpers'
import toast from 'react-hot-toast'

export default function Onboarding() {
  const navigate = useNavigate()
  const { setUser } = useAuthStore()
  const {
    step, setStep,
    selectedGenreIds, selectedGenreNames, toggleGenre,
    followedUserIds, toggleFollow,
  } = useOnboardingStore()

  const { data: genres = [] } = useQuery({
    queryKey: ['genres'],
    queryFn: () => movieService.getGenres().then(r => r.data),
  })

  const saveGenresMutation = useMutation({
    mutationFn: () => onboardingService.saveGenres(selectedGenreIds, selectedGenreNames),
    onSuccess: () => setStep(2),
    onError: () => toast.error('Failed to save genres'),
  })

  const { data: suggestions = [], refetch: refetchSuggestions } = useQuery({
    queryKey: ['onboarding-suggestions'],
    queryFn: () => onboardingService.getSuggestions().then(r => r.data),
    enabled: step === 2,
  })

  const completeMutation = useMutation({
    mutationFn: () => onboardingService.complete(),
    onSuccess: async () => {
      const me = await import('@/services/auth.service').then(m => m.authService.getMe())
      setUser(me.data)
      navigate('/')
    },
    onError: () => toast.error('Something went wrong'),
  })

  const followMutation = useMutation({
    mutationFn: (username: string) => userService.follow(username),
  })

  const handleFollowToggle = (username: string, userId: string) => {
    toggleFollow(userId)
    if (!followedUserIds.includes(userId)) {
      followMutation.mutate(username)
    }
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <Film className="w-8 h-8 text-brand-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Welcome to FilmTracker</h1>
            <p className="text-gray-400 text-sm">Let's personalize your experience</p>
          </div>
        </div>

        {/* Progress dots */}
        <div className="flex gap-2 mb-8">
          {[1, 2].map(s => (
            <div key={s} className={cn(
              'h-1 rounded-full flex-1 transition-colors',
              s <= step ? 'bg-brand-500' : 'bg-surface-border'
            )} />
          ))}
        </div>

        {/* ── Step 1: Genre picker ── */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-white">What genres do you love?</h2>
              <p className="text-gray-400 text-sm mt-1">Pick at least 1 to find people with similar taste.</p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {genres.map((g: { id: number; name: string }) => {
                const selected = selectedGenreIds.includes(g.id)
                return (
                  <button
                    key={g.id}
                    onClick={() => toggleGenre(g.id, g.name)}
                    className={cn(
                      'flex items-center justify-between px-4 py-3 rounded-xl border text-sm font-medium transition-all',
                      selected
                        ? 'bg-brand-600/20 border-brand-500 text-brand-300'
                        : 'bg-surface-muted border-surface-border text-gray-300 hover:border-brand-600/50 hover:text-white'
                    )}
                  >
                    {g.name}
                    {selected && <Check className="w-4 h-4 flex-shrink-0" />}
                  </button>
                )
              })}
            </div>

            <Button
              className="w-full"
              size="lg"
              disabled={selectedGenreIds.length === 0}
              loading={saveGenresMutation.isPending}
              onClick={() => saveGenresMutation.mutate()}
            >
              Continue
            </Button>
          </div>
        )}

        {/* ── Step 2: Suggested users ── */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-bold text-white">People you might like</h2>
              <p className="text-gray-400 text-sm mt-1">
                Follow at least 1 person to start filling your feed.
              </p>
            </div>

            {suggestions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No suggestions yet — more will appear as people join!</p>
              </div>
            ) : (
              <ul className="space-y-3">
                {suggestions.map((u: any) => (
                  <li key={u.id} className="flex items-center gap-3 p-3 rounded-xl bg-surface-card border border-surface-border">
                    <Avatar src={u.avatar_url} username={u.username} size="md" />
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-white text-sm truncate">
                        {u.display_name || u.username}
                      </p>
                      <p className="text-xs text-gray-500">@{u.username} · {u.rating_count} ratings</p>
                    </div>
                    <FollowButton
                      username={u.username}
                      isFollowing={followedUserIds.includes(u.id)}
                      onToggle={() => handleFollowToggle(u.username, u.id)}
                    />
                  </li>
                ))}
              </ul>
            )}

            <div className="flex gap-3">
              <Button variant="ghost" onClick={() => completeMutation.mutate()} className="flex-1">
                Skip for now
              </Button>
              <Button
                className="flex-1"
                size="lg"
                loading={completeMutation.isPending}
                onClick={() => completeMutation.mutate()}
              >
                Go to Feed
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
