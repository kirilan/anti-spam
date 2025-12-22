// User and Auth types
export interface User {
  id: string
  email: string
  google_id: string
  is_admin: boolean
  last_scan_at?: string
  created_at: string
  updated_at: string
}

export interface AuthStatus {
  is_authenticated: boolean
  user: User | null
  message: string
  token?: string | null
}

// Broker types
export interface Broker {
  id: string
  name: string
  domains: string[]
  privacy_email?: string | null
  opt_out_url?: string | null
  category?: string | null
  created_at: string
  updated_at: string
}

export interface BrokerCreateInput {
  name: string
  domains: string[]
  privacy_email?: string | null
  opt_out_url?: string | null
  category?: string | null
}

// Email scan types
export interface EmailScan {
  id: string
  user_id: string
  broker_id: string | null
  gmail_message_id: string
  gmail_thread_id: string | null
  email_direction: 'sent' | 'received'
  sender_email: string
  sender_domain: string
  recipient_email?: string
  subject: string | null
  received_date: string | null
  is_broker_email: boolean
  confidence_score: number | null
  classification_notes: string | null
  body_preview: string | null
  created_at: string
}

export interface EmailScanPage {
  items: EmailScan[]
  total: number
  limit: number
  offset: number
}

export interface ScanHistoryEntry {
  id: string
  performed_at: string
  scan_type: string
  source: string
  days_back: number | null
  max_emails: number | null
  total_scanned: number | null
  broker_emails_found: number | null
  sent_requests_scanned: number | null
  responses_found: number | null
  responses_updated: number | null
  requests_updated: number | null
  message: string
}

export interface ScanHistoryPage {
  items: ScanHistoryEntry[]
  total: number
  limit: number
  offset: number
}

export interface ScanRequest {
  days_back: number
  max_emails: number
}

export interface ScanResult {
  total_scanned: number
  broker_emails_found: number
  scans: EmailScan[]
}

// Deletion request types
export type RequestStatus = 'pending' | 'sent' | 'confirmed' | 'rejected'

export interface DeletionRequest {
  id: string
  user_id: string
  broker_id: string
  status: RequestStatus
  generated_email_subject: string | null
  generated_email_body: string | null
  sent_at: string | null
  confirmed_at: string | null
  rejected_at: string | null
  gmail_sent_message_id?: string | null
  gmail_thread_id?: string | null
  send_attempts?: number
  last_send_error?: string | null
  next_retry_at?: string | null
  notes: string | null
  created_at: string
  updated_at: string
   warning?: string | null
}

export interface DeletionRequestCreate {
  broker_id: string
  framework?: string
}

export interface EmailPreview {
  subject: string
  body: string
  to_email: string | null
  broker_name: string
}

export interface ThreadEmail {
  id: string
  gmail_message_id: string
  gmail_thread_id: string | null
  sender_email: string
  recipient_email: string | null
  subject: string | null
  body_preview: string | null
  direction: 'sent' | 'received'
  received_date: string | null
  response_type: BrokerResponseType | null
  confidence_score: number | null
}

// AI settings/types
export interface AiSettingsStatus {
  has_key: boolean
  updated_at: string | null
  model: string
  available_models: string[]
}

export interface AiClassifyResult {
  request_id: string
  updated_responses: number
  status_updated: boolean
  request_status: RequestStatus
  model: string
  ai_output: AiThreadClassification
}

export interface AiResponseClassification {
  response_id: string
  response_type: BrokerResponseType
  confidence_score: number
  rationale?: string | null
}

export interface AiThreadClassification {
  model: string
  responses: AiResponseClassification[]
}

// Task types
export interface TaskResponse {
  task_id: string
  status: string
}

export interface TaskStatus {
  task_id: string
  state: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
  info?: {
    current?: number
    total?: number
    status?: string
    error?: string
  }
  result?: {
    total_scanned: number
    broker_emails_found: number
    status: string
  }
}

export interface WorkerHealth {
  name: string
  status: 'online' | 'offline'
  active_tasks: number
  queued_tasks: number
  scheduled_tasks: number
  total_tasks: number
  concurrency?: number | null
  uptime?: number | null
}

export interface TaskQueueHealth {
  workers_online: number
  total_active_tasks: number
  total_queued_tasks: number
  workers: WorkerHealth[]
  last_updated: string
}

// Generated email for preview
export interface GeneratedEmail {
  to_email: string
  subject: string
  body: string
}

// Broker response types
export type BrokerResponseType = 'confirmation' | 'rejection' | 'acknowledgment' | 'request_info' | 'unknown'

export interface BrokerResponse {
  id: string
  user_id: string
  deletion_request_id: string | null
  gmail_message_id: string
  gmail_thread_id: string | null
  sender_email: string
  subject: string | null
  body_text: string | null
  received_date: string | null
  response_type: BrokerResponseType
  confidence_score: number | null
  matched_by: string | null
  is_processed: boolean
  processed_at: string | null
  created_at: string
}

// Activity Log types
export type ActivityType =
  | 'request_created'
  | 'request_sent'
  | 'response_received'
  | 'response_scanned'
  | 'email_scanned'
  | 'broker_detected'
  | 'error'
  | 'warning'
  | 'info'

export interface Activity {
  id: string
  user_id: string
  activity_type: ActivityType
  message: string
  details: string | null
  broker_id: string | null
  deletion_request_id: string | null
  response_id: string | null
  email_scan_id: string | null
  created_at: string
}
