import { http, HttpResponse } from 'msw'

// Mock data factories
export const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  google_id: 'google-123',
  is_admin: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

export const mockBroker = {
  id: 'broker-123',
  name: 'Test Broker',
  website: 'https://testbroker.com',
  privacy_email: 'privacy@testbroker.com',
  domains: ['testbroker.com'],
  opt_out_url: 'https://testbroker.com/optout',
  category: 'Data Broker',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

export const mockEmailScan = {
  id: 'scan-123',
  user_id: 'user-123',
  gmail_message_id: 'gmail-msg-123',
  sender_email: 'promo@testbroker.com',
  sender_domain: 'testbroker.com',
  subject: 'Your data profile',
  is_broker_email: true,
  confidence_score: 0.95,
  broker_id: 'broker-123',
  created_at: '2024-01-01T00:00:00Z',
}

export const mockDeletionRequest = {
  id: 'request-123',
  user_id: 'user-123',
  broker_id: 'broker-123',
  status: 'pending',
  generated_email_subject: 'Data Deletion Request',
  generated_email_body: 'Please delete my data...',
  send_attempts: 0,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

export const mockBrokerResponse = {
  id: 'response-123',
  request_id: 'request-123',
  gmail_message_id: 'gmail-resp-123',
  response_type: 'confirmation',
  confidence_score: 0.9,
  subject: 'Re: Data Deletion Request',
  body_preview: 'Your data has been deleted...',
  received_at: '2024-01-02T00:00:00Z',
  created_at: '2024-01-02T00:00:00Z',
}

export const mockAnalytics = {
  total_requests: 10,
  pending_requests: 2,
  sent_requests: 5,
  confirmed_deletions: 3,
  success_rate: 60,
  avg_response_time_days: 2,
}

export const mockTaskStatus = {
  task_id: 'task-123',
  status: 'completed',
  result: { success: true },
}

// API Handlers
export const handlers = [
  // Auth endpoints
  http.get('/auth/status', () => {
    return HttpResponse.json({
      authenticated: true,
      user: mockUser,
    })
  }),

  http.get('/auth/login', () => {
    return HttpResponse.json({
      authorization_url: 'https://accounts.google.com/oauth?...',
      state: 'state-123',
    })
  }),

  http.get('/auth/callback', () => {
    return HttpResponse.json({
      message: 'Authentication successful',
      user_id: 'user-123',
      email: 'test@example.com',
    })
  }),

  http.post('/auth/logout', () => {
    return HttpResponse.json({ message: 'Logged out successfully' })
  }),

  // Brokers endpoints
  http.get('/brokers/', () => {
    return HttpResponse.json([mockBroker])
  }),

  http.get('/brokers/:id', ({ params }) => {
    return HttpResponse.json({ ...mockBroker, id: params.id })
  }),

  http.post('/brokers/', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>
    return HttpResponse.json({ ...mockBroker, ...body, id: 'new-broker-123' })
  }),

  http.post('/brokers/sync', () => {
    return HttpResponse.json({ message: 'Synced 15 brokers' })
  }),

  // Emails endpoints
  http.get('/emails/scans', () => {
    return HttpResponse.json({
      items: [mockEmailScan],
      total: 1,
      limit: 50,
      offset: 0,
    })
  }),

  http.post('/emails/scan', () => {
    return HttpResponse.json({
      task_id: 'task-scan-123',
      status: 'pending',
    })
  }),

  http.get('/emails/scan-history', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'history-123',
          performed_at: '2024-01-01T00:00:00Z',
          scan_type: 'email_scan',
          source: 'manual',
          days_back: 30,
          max_emails: 100,
          total_scanned: 50,
          broker_emails_found: 5,
          message: 'Scan completed successfully',
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
    })
  }),

  // Requests endpoints
  http.get('/requests/', () => {
    return HttpResponse.json([mockDeletionRequest])
  }),

  http.get('/requests/:id', ({ params }) => {
    return HttpResponse.json({ ...mockDeletionRequest, id: params.id })
  }),

  http.post('/requests/', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>
    return HttpResponse.json({ ...mockDeletionRequest, ...body, id: 'new-request-123' })
  }),

  http.post('/requests/:id/send', () => {
    return HttpResponse.json({
      ...mockDeletionRequest,
      status: 'sent',
    })
  }),

  http.put('/requests/:id/status', async ({ params, request }) => {
    const body = (await request.json()) as { status: string; notes?: string }
    return HttpResponse.json({
      ...mockDeletionRequest,
      id: params.id,
      status: body.status,
    })
  }),

  http.get('/requests/:id/email-preview', () => {
    return HttpResponse.json({
      to_email: 'privacy@testbroker.com',
      subject: 'Data Deletion Request - GDPR',
      body: 'Dear Privacy Team,\n\nPlease delete my data...',
    })
  }),

  http.post('/requests/:id/ai-classify', () => {
    return HttpResponse.json({
      request_id: 'request-123',
      updated_responses: 1,
      status_updated: true,
      request_status: 'confirmed',
      model: 'gemini-2.0-flash',
      ai_output: {
        model: 'gemini-2.0-flash',
        responses: [],
      },
    })
  }),

  // Responses endpoints
  http.get('/responses/', () => {
    return HttpResponse.json([mockBrokerResponse])
  }),

  http.post('/responses/scan', () => {
    return HttpResponse.json({
      task_id: 'task-resp-scan-123',
      status: 'pending',
    })
  }),

  http.patch('/responses/:id', async ({ params, request }) => {
    const body = (await request.json()) as Record<string, unknown>
    return HttpResponse.json({ ...mockBrokerResponse, id: params.id, ...body })
  }),

  // Tasks endpoints
  http.get('/tasks/:id', ({ params }) => {
    return HttpResponse.json({ ...mockTaskStatus, task_id: params.id })
  }),

  http.delete('/tasks/:id', () => {
    return HttpResponse.json({ message: 'Task cancelled' })
  }),

  http.get('/tasks/health', () => {
    return HttpResponse.json({
      workers_active: 2,
      tasks_queued: 5,
      tasks_active: 1,
    })
  }),

  http.post('/tasks/scan', () => {
    return HttpResponse.json({
      task_id: 'task-scan-123',
      status: 'pending',
    })
  }),

  // Analytics endpoints
  http.get('/analytics/stats', () => {
    return HttpResponse.json(mockAnalytics)
  }),

  http.get('/analytics/broker-ranking', () => {
    return HttpResponse.json([
      {
        broker_id: 'broker-123',
        broker_name: 'Test Broker',
        total_requests: 5,
        confirmations: 3,
        success_rate: 60,
        avg_response_time_days: 2,
      },
    ])
  }),

  http.get('/analytics/timeline', () => {
    return HttpResponse.json([
      { date: '2024-01-01', requests_sent: 5, confirmations_received: 2 },
      { date: '2024-01-02', requests_sent: 3, confirmations_received: 1 },
    ])
  }),

  http.get('/analytics/response-distribution', () => {
    return HttpResponse.json([
      { response_type: 'confirmation', count: 3, percentage: 42.9 },
      { response_type: 'rejection', count: 1, percentage: 14.3 },
      { response_type: 'acknowledgment', count: 2, percentage: 28.6 },
      { response_type: 'request_info', count: 1, percentage: 14.3 },
    ])
  }),

  // Activities endpoints
  http.get('/activities/', () => {
    return HttpResponse.json([
      {
        id: 'activity-123',
        user_id: 'user-123',
        activity_type: 'request_created',
        description: 'Created deletion request',
        created_at: '2024-01-01T00:00:00Z',
      },
    ])
  }),

  // Admin endpoints
  http.get('/admin/users', () => {
    return HttpResponse.json([mockUser])
  }),

  http.patch('/admin/users/:id/role', async ({ params, request }) => {
    const body = (await request.json()) as Record<string, unknown>
    return HttpResponse.json({ ...mockUser, id: params.id, ...body })
  }),

  http.post('/admin/users/:id/revoke-tokens', () => {
    return HttpResponse.json({ message: 'Tokens revoked successfully' })
  }),

  // AI endpoints
  http.get('/ai/key/status', () => {
    return HttpResponse.json({
      has_key: false,
      model: 'gemini-2.0-flash',
      available_models: ['gemini-2.0-flash', 'gemini-1.5-pro'],
    })
  }),

  http.put('/ai/key', async ({ request }) => {
    const body = (await request.json()) as { api_key?: string; model?: string }
    return HttpResponse.json({
      has_key: !!body.api_key,
      model: body.model || 'gemini-2.0-flash',
      available_models: ['gemini-2.0-flash', 'gemini-1.5-pro'],
    })
  }),

  http.delete('/ai/key', () => {
    return HttpResponse.json({
      has_key: false,
      model: 'gemini-2.0-flash',
      available_models: ['gemini-2.0-flash', 'gemini-1.5-pro'],
    })
  }),
]
