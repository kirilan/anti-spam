import { create } from 'zustand'

export interface RateLimitNotice {
  message: string
  retryAfter?: number
  triggeredAt: number
}

interface RateLimitState {
  notice: RateLimitNotice | null
  setNotice: (notice: RateLimitNotice) => void
  clearNotice: () => void
}

export const useRateLimitStore = create<RateLimitState>((set) => ({
  notice: null,
  setNotice: (notice) => set({ notice }),
  clearNotice: () => set({ notice: null }),
}))
