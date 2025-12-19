import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { requestsApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'

export function useRequests() {
  const { userId } = useAuthStore()

  return useQuery({
    queryKey: ['requests', userId],
    queryFn: () => requestsApi.list(userId!),
    enabled: !!userId,
  })
}

export function useRequest(requestId: string) {
  return useQuery({
    queryKey: ['request', requestId],
    queryFn: () => requestsApi.get(requestId),
    enabled: !!requestId,
  })
}

export function useCreateRequest() {
  const { userId } = useAuthStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (brokerId: string) => requestsApi.create(userId!, { broker_id: brokerId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'stats'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'timeline'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'broker-ranking'] })
    },
  })
}

export function useUpdateRequestStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      requestId,
      status,
      notes,
    }: {
      requestId: string
      status: string
      notes?: string
    }) => requestsApi.updateStatus(requestId, status, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'stats'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'timeline'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'broker-ranking'] })
    },
  })
}

export function useEmailPreview(requestId: string) {
  return useQuery({
    queryKey: ['emailPreview', requestId],
    queryFn: () => requestsApi.getEmailPreview(requestId),
    enabled: !!requestId,
  })
}
