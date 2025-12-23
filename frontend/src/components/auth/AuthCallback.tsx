import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

export function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setSession } = useAuthStore()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = () => {
      const userId = searchParams.get('user_id')
      const token = searchParams.get('token')

      if (!userId || !token) {
        setError('Missing authentication data')
        return
      }

      try {
        setSession(userId, token)
        navigate('/dashboard', { replace: true })
      } catch (err) {
        console.error('Auth callback error:', err)
        setError('Authentication failed. Please try again.')
      }
    }

    handleCallback()
  }, [searchParams, navigate, setSession])

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <a href="/" className="text-primary hover:underline">
            Return to login
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto mb-4" />
        <p className="text-muted-foreground">Completing authentication...</p>
      </div>
    </div>
  )
}
