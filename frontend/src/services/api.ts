import axios from 'axios'
import type {
  AuthStatus,
  Broker,
  EmailScan,
  DeletionRequest,
  DeletionRequestCreate,
  EmailPreview,
  TaskResponse,
  TaskStatus,
  ScanRequest,
  BrokerResponse,
} from '@/types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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

  getStatus: async (userId: string) => {
    const response = await api.get<AuthStatus>(`/auth/status?user_id=${userId}`)
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

  sync: async () => {
    const response = await api.post<{ message: string; brokers_added: number; total_brokers: number }>(
      '/brokers/sync'
    )
    return response.data
  },
}

// Emails API
export const emailsApi = {
  scan: async (userId: string, params: ScanRequest) => {
    const response = await api.post(`/emails/scan?user_id=${userId}`, params)
    return response.data
  },

  getScans: async (userId: string, brokerOnly = false, limit = 1000) => {
    const response = await api.get<EmailScan[]>(
      `/emails/scans?user_id=${userId}&broker_only=${brokerOnly}&limit=${limit}`
    )
    return response.data
  },
}

// Deletion Requests API
export const requestsApi = {
  create: async (userId: string, data: DeletionRequestCreate) => {
    const response = await api.post<DeletionRequest>(`/requests/?user_id=${userId}`, data)
    return response.data
  },

  list: async (userId: string) => {
    const response = await api.get<DeletionRequest[]>(`/requests/?user_id=${userId}`)
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
}

// Tasks API
export const tasksApi = {
  startScan: async (userId: string, daysBack = 30, maxEmails = 300) => {
    const response = await api.post<TaskResponse>(`/tasks/scan?user_id=${userId}`, {
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
}

// Responses API
export const responsesApi = {
  list: async (userId: string, requestId?: string) => {
    const params = new URLSearchParams({ user_id: userId })
    if (requestId) {
      params.append('request_id', requestId)
    }
    const response = await api.get<BrokerResponse[]>(`/responses/?${params}`)
    return response.data
  },

  get: async (responseId: string) => {
    const response = await api.get<BrokerResponse>(`/responses/${responseId}`)
    return response.data
  },

  scanResponses: async (userId: string, daysBack: number = 7) => {
    const response = await api.post<TaskResponse>(`/responses/scan?user_id=${userId}&days_back=${daysBack}`)
    return response.data
  },
}

// Analytics API
export const analyticsApi = {
  getStats: async (userId: string) => {
    const response = await api.get(`/analytics/stats?user_id=${userId}`)
    return response.data
  },

  getBrokerRanking: async (userId?: string) => {
    const params = userId ? `?user_id=${userId}` : ''
    const response = await api.get(`/analytics/broker-ranking${params}`)
    return response.data
  },

  getTimeline: async (userId: string, days: number = 30) => {
    const response = await api.get(`/analytics/timeline?user_id=${userId}&days=${days}`)
    return response.data
  },

  getResponseDistribution: async (userId: string) => {
    const response = await api.get(`/analytics/response-distribution?user_id=${userId}`)
    return response.data
  },
}

export default api
