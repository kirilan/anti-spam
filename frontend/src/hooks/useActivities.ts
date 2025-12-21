import { useQuery } from '@tanstack/react-query'
import { activitiesApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'

export function useActivities(
  brokerId?: string | null,
  activityType?: string | null,
  daysBack = 30
) {
  const { userId } = useAuthStore()

  return useQuery({
    queryKey: ['activities', userId, brokerId, activityType, daysBack],
    queryFn: () => activitiesApi.list(brokerId, activityType, daysBack),
    enabled: !!userId,
  })
}
