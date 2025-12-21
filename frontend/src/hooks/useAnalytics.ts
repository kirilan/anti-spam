import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'

export interface AnalyticsStats {
  total_requests: number
  sent_requests: number
  confirmed_deletions: number
  pending_requests: number
  success_rate: number
  avg_response_time_days: number | null
}

export interface BrokerRanking {
  broker_id: string
  broker_name: string
  total_requests: number
  confirmations: number
  success_rate: number
  avg_response_time_days: number | null
}

export interface TimelineData {
  date: string
  requests_sent: number
  confirmations_received: number
}

export interface ResponseDistribution {
  response_type: string
  count: number
  percentage: number
}

export function useAnalytics() {
  const { userId } = useAuthStore()

  return useQuery<AnalyticsStats>({
    queryKey: ['analytics', 'stats', userId],
    queryFn: () => analyticsApi.getStats(),
    enabled: !!userId,
  })
}

export function useBrokerRanking(userIdParam?: string) {
  const { userId: authUserId } = useAuthStore()
  const userId = userIdParam || authUserId

  return useQuery<BrokerRanking[]>({
    queryKey: ['analytics', 'broker-ranking', userId],
    queryFn: () => analyticsApi.getBrokerRanking(userId || undefined),
    enabled: !!userId,
  })
}

export function useTimeline(days: number = 30) {
  const { userId } = useAuthStore()

  return useQuery<TimelineData[]>({
    queryKey: ['analytics', 'timeline', userId, days],
    queryFn: () => analyticsApi.getTimeline(days),
    enabled: !!userId,
  })
}

export function useResponseDistribution() {
  const { userId } = useAuthStore()

  return useQuery<ResponseDistribution[]>({
    queryKey: ['analytics', 'response-distribution', userId],
    queryFn: () => analyticsApi.getResponseDistribution(),
    enabled: !!userId,
  })
}
