import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { useRateLimitStore } from '@/stores/rateLimitStore'
import type {
  AuthStatus,
  Broker,
  BrokerCreateInput,
  EmailScan,
  DeletionRequest,
  DeletionRequestCreate,
  EmailPreview,
  TaskResponse,
  TaskStatus,
  ScanRequest,
  BrokerResponse,
  TaskQueueHealth,
  User,
  AiSettingsStatus,
  AiClassifyResult,
  EmailScanPage,
  ScanHistoryPage,
  ThreadEmail,
} from '@/types'

// Use empty string for production (nginx proxies /api, /auth, etc.)
// Use full URL for local Vite dev server (e.g., 'http://localhost:8000')
const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const { token } = useAuthStore.getState()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    if (status === 429) {
      const detail =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Too many requests. Please slow down.'
      const retryHeader = error.response?.headers?.['retry-after']
      const retryAfter = retryHeader ? Number(retryHeader) : undefined
      useRateLimitStore
        .getState()
        .setNotice({
          message: detail,
          retryAfter: Number.isFinite(retryAfter) ? retryAfter : undefined,
          triggeredAt: Date.now(),
        })
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async () => {
    const response = await api.get<{ authorization_url: string; state: string }>('/auth/login')
    return response.data
  },

  callback: async (code: string, state: string) => {
    const response = await api.get<{ message: string; user_id: string; email: string }>(
      `/auth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
    )
    return response.data
  },

  getStatus: async () => {
    const response = await api.get<AuthStatus>('/auth/status')
    return response.data
  },
}

// Brokers API
export const brokersApi = {
  list: async () => {
    const response = await api.get<Broker[]>('/brokers/')
    return response.data
  },

  get: async (brokerId: string) => {
    const response = await api.get<Broker>(`/brokers/${brokerId}`)
    return response.data
  },

  create: async (data: BrokerCreateInput) => {
    const response = await api.post<Broker>('/brokers/', data)
    return response.data
  },

  sync: async () => {
    const response = await api.post<{ message: string; brokers_added: number; total_brokers: number }>(
      '/brokers/sync'
    )
    return response.data
  },
}

// Emails API
export const emailsApi = {
  scan: async (params: ScanRequest) => {
    // Backend uses authenticated user from JWT
    const response = await api.post(`/emails/scan`, params)
    return response.data
  },

  getScans: async (brokerOnly = false, limit = 1000) => {
    // Backend uses authenticated user from JWT
    const response = await api.get<EmailScan[]>(
      `/emails/scans?broker_only=${brokerOnly}&limit=${limit}`
    )
    return response.data
  },

  getScansPaged: async (direction: 'all' | 'sent' | 'received' = 'all', limit = 10, offset = 0) => {
    // Backend uses authenticated user from JWT
    // Note: Backend now always filters to broker emails only
    const response = await api.get<EmailScanPage>(
      `/emails/scans/paged?direction=${direction}&limit=${limit}&offset=${offset}`
    )
    return response.data
  },

  getScanHistory: async (limit = 10, offset = 0) => {
    // Backend uses authenticated user from JWT
    const response = await api.get<ScanHistoryPage>(
      `/emails/scan-history?limit=${limit}&offset=${offset}`
    )
    return response.data
  },
}

// Deletion Requests API
export const requestsApi = {
  create: async (data: DeletionRequestCreate) => {
    // Backend uses authenticated user from JWT
    const response = await api.post<DeletionRequest>(`/requests/`, data)
    return response.data
  },

  list: async () => {
    // Backend uses authenticated user from JWT
    const response = await api.get<DeletionRequest[]>(`/requests/`)
    return response.data
  },

  get: async (requestId: string) => {
    const response = await api.get<DeletionRequest>(`/requests/${requestId}`)
    return response.data
  },

  updateStatus: async (requestId: string, status: string, notes?: string) => {
    const response = await api.put<DeletionRequest>(`/requests/${requestId}/status`, {
      status,
      notes,
    })
    return response.data
  },

  getEmailPreview: async (requestId: string) => {
    const response = await api.get<EmailPreview>(`/requests/${requestId}/email-preview`)
    return response.data
  },

  previewEmail: async (requestId: string) => {
    const response = await api.get<{ to_email: string; subject: string; body: string }>(
      `/requests/${requestId}/email-preview`
    )
    return response.data
  },

  sendRequest: async (requestId: string) => {
    const response = await api.post<DeletionRequest>(`/requests/${requestId}/send`)
    return response.data
  },

  aiClassify: async (requestId: string) => {
    const response = await api.post<AiClassifyResult>(`/requests/${requestId}/ai-classify`)
    return response.data
  },

  getThread: async (requestId: string) => {
    const response = await api.get<ThreadEmail[]>(`/requests/${requestId}/thread`)
    return response.data
  },
}

// Tasks API
export const tasksApi = {
  startScan: async (daysBack = 1, maxEmails = 100) => {
    // Backend uses authenticated user from JWT
    const response = await api.post<TaskResponse>(`/tasks/scan`, {
      days_back: daysBack,
      max_emails: maxEmails,
    })
    return response.data
  },

  getTaskStatus: async (taskId: string) => {
    const response = await api.get<TaskStatus>(`/tasks/${taskId}`)
    return response.data
  },

  cancel: async (taskId: string) => {
    const response = await api.delete(`/tasks/${taskId}`)
    return response.data
  },

  getHealth: async () => {
    const response = await api.get<TaskQueueHealth>('/tasks/health')
    return response.data
  },
}

// Responses API
export const responsesApi = {
  list: async (requestId?: string) => {
    // Backend uses authenticated user from JWT, no userId param needed
    const params = new URLSearchParams()
    if (requestId) {
      params.append('request_id', requestId)
    }
    const queryString = params.toString()
    const response = await api.get<BrokerResponse[]>(`/responses/${queryString ? `?${queryString}` : ''}`)
    return response.data
  },

  get: async (responseId: string) => {
    const response = await api.get<BrokerResponse>(`/responses/${responseId}`)
    return response.data
  },

  scanResponses: async (daysBack: number = 7) => {
    // Backend uses authenticated user from JWT, no userId param needed
    const response = await api.post<TaskResponse>(`/responses/scan?days_back=${daysBack}`)
    return response.data
  },

  classify: async (
    responseId: string,
    payload: { response_type: BrokerResponse['response_type']; deletion_request_id?: string | null }
  ) => {
    const response = await api.patch<BrokerResponse>(`/responses/${responseId}/classify`, payload)
    return response.data
  },
}

// AI Settings API
export const aiApi = {
  getKeyStatus: async () => {
    const response = await api.get<AiSettingsStatus>('/ai/key/status')
    return response.data
  },

  setKey: async (payload: { api_key?: string; model?: string }) => {
    const response = await api.put<AiSettingsStatus>('/ai/key', payload)
    return response.data
  },

  deleteKey: async () => {
    const response = await api.delete<AiSettingsStatus>('/ai/key')
    return response.data
  },
}

// Analytics API
export const analyticsApi = {
  getStats: async () => {
    // Backend uses authenticated user from JWT, no userId param needed
    const response = await api.get(`/analytics/stats`)
    return response.data
  },

  getBrokerRanking: async (userId?: string) => {
    const params = userId ? `?user_id=${userId}` : ''
    const response = await api.get(`/analytics/broker-ranking${params}`)
    return response.data
  },

  getTimeline: async (days: number = 30) => {
    // Backend uses authenticated user from JWT, no userId param needed
    const response = await api.get(`/analytics/timeline?days=${days}`)
    return response.data
  },

  getResponseDistribution: async () => {
    // Backend uses authenticated user from JWT, no userId param needed
    const response = await api.get(`/analytics/response-distribution`)
    return response.data
  },
}

// Activities API
export const activitiesApi = {
  list: async (
    brokerId?: string | null,
    activityType?: string | null,
    daysBack = 30
  ) => {
    // Backend uses authenticated user from JWT, no userId param needed
    const params = new URLSearchParams({ days_back: String(daysBack) })
    if (brokerId) params.append('broker_id', brokerId)
    if (activityType) params.append('activity_type', activityType)

    const response = await api.get(`/activities/?${params}`)
    return response.data
  }
}

// Admin API
export const adminApi = {
  listUsers: async () => {
    const response = await api.get<User[]>('/admin/users')
    return response.data
  },

  updateUserRole: async (userId: string, isAdmin: boolean) => {
    const response = await api.patch<User>(`/admin/users/${userId}/role`, {
      is_admin: isAdmin,
    })
    return response.data
  },

  revokeTokens: async (userId: string) => {
    const response = await api.post<{ message: string }>(`/admin/users/${userId}/revoke-tokens`)
    return response.data
  },
}

export default api
