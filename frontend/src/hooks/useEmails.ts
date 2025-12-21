import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { emailsApi, tasksApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import type { ScanRequest } from '@/types'

export function useEmailScans(brokerOnly = false, limit = 1000) {
  const { userId } = useAuthStore()

  return useQuery({
    queryKey: ['emailScans', userId, brokerOnly, limit],
    queryFn: () => emailsApi.getScans(brokerOnly, limit),
    enabled: !!userId,
    staleTime: 0, // Always refetch to get latest data
  })
}

export function useEmailScansPaged(brokerOnly: boolean, limit: number, offset: number) {
  const { userId } = useAuthStore()

  return useQuery({
    queryKey: ['emailScansPaged', userId, brokerOnly, limit, offset],
    queryFn: () => emailsApi.getScansPaged(brokerOnly, limit, offset),
    enabled: !!userId,
    staleTime: 0,
  })
}

export function useScanHistory(limit: number, offset: number) {
  const { userId } = useAuthStore()

  return useQuery({
    queryKey: ['scanHistory', userId, limit, offset],
    queryFn: () => emailsApi.getScanHistory(limit, offset),
    enabled: !!userId,
    staleTime: 0,
  })
}

export function useScanInbox() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (params: ScanRequest) => emailsApi.scan(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emailScans'] })
    },
  })
}

export function useStartScanTask() {
  return useMutation({
    mutationFn: ({ daysBack, maxEmails }: { daysBack: number; maxEmails: number }) =>
      tasksApi.startScan(daysBack, maxEmails),
  })
}

export function useTaskStatus(taskId: string | null) {
  const queryClient = useQueryClient()

  return useQuery({
    queryKey: ['taskStatus', taskId],
    queryFn: () => tasksApi.getTaskStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data?.state === 'SUCCESS' || data?.state === 'FAILURE') {
        // Invalidate email scans when task completes
        queryClient.invalidateQueries({ queryKey: ['emailScans'] })
        queryClient.invalidateQueries({ queryKey: ['emailScansPaged'] })
        queryClient.invalidateQueries({ queryKey: ['scanHistory'] })
        return false
      }
      return 2000 // Poll every 2 seconds
    },
  })
}
