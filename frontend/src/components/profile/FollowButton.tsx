import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { userService } from '@/services/user.service'
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

interface FollowButtonProps {
  username: string
  isFollowing: boolean
  onToggle?: (nowFollowing: boolean) => void
}

export function FollowButton({ username, isFollowing, onToggle }: FollowButtonProps) {
  const { currentUser } = useAuthStore()
  const qc = useQueryClient()
  const [optimistic, setOptimistic] = useState(isFollowing)

  if (currentUser?.username === username) return null

  const mutation = useMutation({
    mutationFn: () =>
      optimistic ? userService.unfollow(username) : userService.follow(username),
    onMutate: () => {
      const next = !optimistic
      setOptimistic(next)
      onToggle?.(next)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile', username] })
      qc.invalidateQueries({ queryKey: ['feed'] })
    },
    onError: () => {
      setOptimistic(v => !v)
      onToggle?.(optimistic)
      toast.error('Something went wrong')
    },
  })

  return (
    <Button
      variant={optimistic ? 'outline' : 'primary'}
      size="sm"
      loading={mutation.isPending}
      onClick={() => mutation.mutate()}
    >
      {optimistic ? 'Following' : 'Follow'}
    </Button>
  )
}
