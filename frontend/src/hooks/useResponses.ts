import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { responsesApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import type { BrokerResponse, BrokerResponseType } from '@/types'

export function useResponses(requestId?: string) {
  const { userId } = useAuthStore()

  return useQuery<BrokerResponse[]>({
    queryKey: ['responses', userId, requestId],
    queryFn: () => responsesApi.list(userId!, requestId),
    enabled: !!userId,
  })
}

export function useResponse(responseId: string) {
  return useQuery<BrokerResponse>({
    queryKey: ['response', responseId],
    queryFn: () => responsesApi.get(responseId),
    enabled: !!responseId,
  })
}

export function useScanResponses() {
  const { userId } = useAuthStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (daysBack: number = 7) => responsesApi.scanResponses(userId!, daysBack),
    onSuccess: () => {
      // Invalidate and refetch responses after scan
      queryClient.invalidateQueries({ queryKey: ['responses'] })
      queryClient.invalidateQueries({ queryKey: ['requests'] })
    },
  })
}

export function useClassifyResponse() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      responseId,
      responseType,
      deletionRequestId,
    }: {
      responseId: string
      responseType: BrokerResponseType
      deletionRequestId?: string | null
    }) =>
      responsesApi.classify(responseId, {
        response_type: responseType,
        deletion_request_id: deletionRequestId ?? undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['responses'] })
      queryClient.invalidateQueries({ queryKey: ['requests'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'response-distribution'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'timeline'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'broker-ranking'] })
    },
  })
}
