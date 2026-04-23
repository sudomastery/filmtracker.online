import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Film, Eye, EyeOff } from 'lucide-react'
import { authService } from '@/services/auth.service'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import toast from 'react-hot-toast'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const { setTokens, setUser } = useAuthStore()
  const navigate = useNavigate()

  const mutation = useMutation({
    mutationFn: () => authService.login(username.trim(), password),
    onSuccess: async (res) => {
      setTokens(res.data.access_token, res.data.refresh_token)
      const me = await authService.getMe()
      setUser(me.data)
      if (!me.data.onboarding_complete) {
        navigate('/onboarding')
      } else {
        navigate('/')
      }
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Invalid credentials')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) return
    mutation.mutate()
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-brand-600/20 flex items-center justify-center">
            <Film className="w-8 h-8 text-brand-400" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-white">FilmTracker</h1>
            <p className="text-gray-400 text-sm mt-1">Sign in to your account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
          <Input
            label="Username or Email"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="yourname"
            autoComplete="username"
            autoFocus
          />
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-300">Password</label>
            <div className="relative">
              <input
                type={showPass ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                className="w-full px-4 py-2.5 pr-10 rounded-xl bg-surface-muted border border-surface-border text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPass(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <Button type="submit" className="w-full" size="lg" loading={mutation.isPending}>
            Sign In
          </Button>
        </form>

        <p className="text-center text-sm text-gray-400">
          New to FilmTracker?{' '}
          <Link to="/register" className="text-brand-400 hover:underline font-medium">
            Create account
          </Link>
        </p>
      </div>
    </div>
  )
}
