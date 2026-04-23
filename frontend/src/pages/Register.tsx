import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Film, Eye, EyeOff } from 'lucide-react'
import { authService } from '@/services/auth.service'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import toast from 'react-hot-toast'

export default function Register() {
  const [form, setForm] = useState({ username: '', email: '', password: '', display_name: '' })
  const [showPass, setShowPass] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const { setTokens, setUser } = useAuthStore()
  const navigate = useNavigate()

  const mutation = useMutation({
    mutationFn: () => authService.register(form),
    onSuccess: async (res) => {
      setTokens(res.data.access_token, res.data.refresh_token)
      const me = await authService.getMe()
      setUser(me.data)
      navigate('/onboarding')
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      if (typeof detail === 'string') toast.error(detail)
      else toast.error('Registration failed')
    },
  })

  const validate = () => {
    const e: Record<string, string> = {}
    if (form.username.length < 3) e.username = 'At least 3 characters'
    if (!/^[a-zA-Z0-9_]+$/.test(form.username)) e.username = 'Letters, numbers and _ only'
    if (!form.email.includes('@')) e.email = 'Invalid email'
    if (form.password.length < 8) e.password = 'At least 8 characters'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) mutation.mutate()
  }

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="flex flex-col items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-brand-600/20 flex items-center justify-center">
            <Film className="w-8 h-8 text-brand-400" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-white">Join FilmTracker</h1>
            <p className="text-gray-400 text-sm mt-1">Track movies with friends</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-surface-card border border-surface-border rounded-2xl p-6 space-y-4">
          <Input
            label="Username"
            value={form.username}
            onChange={set('username')}
            placeholder="coolfilmfan"
            error={errors.username}
            autoFocus
          />
          <Input
            label="Display Name"
            value={form.display_name}
            onChange={set('display_name')}
            placeholder="Cool Film Fan (optional)"
          />
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={set('email')}
            placeholder="you@example.com"
            error={errors.email}
          />
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-300">Password</label>
            <div className="relative">
              <input
                type={showPass ? 'text' : 'password'}
                value={form.password}
                onChange={set('password')}
                placeholder="Min 8 characters"
                className="w-full px-4 py-2.5 pr-10 rounded-xl bg-surface-muted border border-surface-border text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors"
              />
              <button type="button" onClick={() => setShowPass(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && <p className="text-red-400 text-xs">{errors.password}</p>}
          </div>

          <Button type="submit" className="w-full" size="lg" loading={mutation.isPending}>
            Create Account
          </Button>
        </form>

        <p className="text-center text-sm text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-400 hover:underline font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
