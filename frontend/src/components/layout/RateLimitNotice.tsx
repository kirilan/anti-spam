import { useEffect, useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import { useRateLimitStore } from '@/stores/rateLimitStore'

function formatRemaining(seconds: number): string {
  if (seconds <= 0) return 'now'
  if (seconds < 60) return `${Math.ceil(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`
}

export function RateLimitNotice() {
  const { notice, clearNotice } = useRateLimitStore()
  const [remaining, setRemaining] = useState<number>(0)

  useEffect(() => {
    const retryAfter = notice?.retryAfter
    if (!retryAfter || retryAfter <= 0) {
      setRemaining(0)
      return
    }

    const updateRemaining = () => {
      const elapsed = (Date.now() - (notice?.triggeredAt ?? Date.now())) / 1000
      setRemaining(Math.max(retryAfter - elapsed, 0))
    }

    updateRemaining()
    const interval = setInterval(updateRemaining, 1000)
    return () => clearInterval(interval)
  }, [notice])

  if (!notice) {
    return null
  }

  return (
    <div className="mb-6 rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3 text-yellow-800 shadow-sm">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5" />
        <div className="flex-1 space-y-1 text-sm">
          <p className="font-medium">Requests temporarily throttled</p>
          <p>{notice.message}</p>
          {notice.retryAfter && (
            <p className="text-xs text-yellow-700">
              Try again in {formatRemaining(remaining)}.
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={clearNotice}
          className="rounded-full p-1 text-yellow-700 hover:bg-yellow-100"
          aria-label="Dismiss rate limit notice"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
