import { useQuery } from '@tanstack/react-query'
import { tasksApi } from '@/services/api'

export function useTaskHealth(enabled = true, refetchInterval = 30000) {
  return useQuery({
    queryKey: ['tasks', 'health'],
    queryFn: tasksApi.getHealth,
    enabled,
    refetchInterval: enabled ? refetchInterval : false,
  })
}
