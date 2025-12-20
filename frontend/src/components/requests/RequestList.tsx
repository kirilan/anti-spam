import { useMemo, useState, type ComponentType } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useRequests, useCreateRequest } from '@/hooks/useRequests'
import { useEmailScans } from '@/hooks/useEmails'
import { useBrokers } from '@/hooks/useBrokers'
import { useResponses, useScanResponses, useClassifyResponse } from '@/hooks/useResponses'
import { DeletionRequest, EmailScan, BrokerResponse, BrokerResponseType, AiClassifyResult } from '@/types'
import { EmailPreviewDialog } from './EmailPreviewDialog'
import { AiResultDialog } from './AiResultDialog'
import { useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Loader2,
  AlertTriangle,
  Clock,
  Mail,
  CheckCircle,
  Plus,
  Eye,
  Send,
  Calendar,
  History,
  MessageSquare,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  HelpCircle,
  XCircle,
  AlertCircle
} from 'lucide-react'

export function RequestList() {
  const { data: requests, isLoading, error, refetch } = useRequests()
  const { data: brokerEmails } = useEmailScans(true)
  const { data: brokers } = useBrokers()
  const { data: responses } = useResponses()
  const scanResponses = useScanResponses()
  const createRequest = useCreateRequest()
  const queryClient = useQueryClient()
  const [previewRequest, setPreviewRequest] = useState<DeletionRequest | null>(null)
  const [creatingFor, setCreatingFor] = useState<string | null>(null)
  const [sendingRequestId, setSendingRequestId] = useState<string | null>(null)
  const [aiProcessingRequestId, setAiProcessingRequestId] = useState<string | null>(null)
  const [aiErrorRequestId, setAiErrorRequestId] = useState<string | null>(null)
  const [aiErrorMessage, setAiErrorMessage] = useState<string | null>(null)
  const [aiResult, setAiResult] = useState<AiClassifyResult | null>(null)
  const [aiResultRequest, setAiResultRequest] = useState<DeletionRequest | null>(null)
  const [scanSuccessMessage, setScanSuccessMessage] = useState<string | null>(null)
  const [scanErrorMessage, setScanErrorMessage] = useState<string | null>(null)
  const [permissionError, setPermissionError] = useState(false)
  const [createWarning, setCreateWarning] = useState<string | null>(null)

  // Create a map of broker IDs to broker names for quick lookup
  const brokerMap = new Map(brokers?.map(b => [b.id, b.name]) || [])
  const responsesByRequest = useMemo(() => {
    const grouped = new Map<string, BrokerResponse[]>()
    responses?.forEach((response) => {
      if (!response.deletion_request_id) {
        return
      }
      if (!grouped.has(response.deletion_request_id)) {
        grouped.set(response.deletion_request_id, [])
      }
      grouped.get(response.deletion_request_id)!.push(response)
    })

    grouped.forEach((items) => {
      items.sort((a, b) => {
        const dateA = new Date(a.received_date || a.created_at).getTime()
        const dateB = new Date(b.received_date || b.created_at).getTime()
        return dateA - dateB
      })
    })

    return grouped
  }, [responses])

  const previewResponses = useMemo(() => {
    if (!previewRequest || !responses) {
      return []
    }
    return responses.filter((response) => (
      response.deletion_request_id === previewRequest.id ||
      (previewRequest.gmail_thread_id && response.gmail_thread_id === previewRequest.gmail_thread_id)
    ))
  }, [previewRequest, responses])

  const handleCreateRequest = async (brokerId: string) => {
    setCreatingFor(brokerId)
    try {
      const result = await createRequest.mutateAsync(brokerId)
      setCreateWarning(result?.warning || null)
    } finally {
      setCreatingFor(null)
    }
  }

  const handleSendEmail = async (requestId: string) => {
    setSendingRequestId(requestId)
    try {
      const { requestsApi } = await import('@/services/api')
      await requestsApi.sendRequest(requestId)
      await refetch() // Refresh the list to show updated status
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'stats'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'timeline'] })
      queryClient.invalidateQueries({ queryKey: ['analytics', 'broker-ranking'] })
    } catch (error: any) {
      console.error('Failed to send email:', error)
      if (error.response?.status === 403 || error.response?.data?.detail?.includes('permission')) {
        setPermissionError(true)
      }
      await refetch()
    } finally {
      setSendingRequestId(null)
    }
  }

  const handleScanResponses = async () => {
    setScanErrorMessage(null)
    setScanSuccessMessage(null)
    try {
      await scanResponses.mutateAsync(7)
      setScanSuccessMessage('Scan complete. Responses updated.')
      setTimeout(() => setScanSuccessMessage(null), 3000)
    } catch (scanError: any) {
      console.error('Failed to scan responses:', scanError)
      setScanErrorMessage(scanError.response?.data?.detail || 'Scan failed.')
      setTimeout(() => setScanErrorMessage(null), 4000)
    }
  }

  const handleAiAssist = async (requestId: string) => {
    setAiProcessingRequestId(requestId)
    setAiErrorRequestId(null)
    setAiErrorMessage(null)
    try {
      const { requestsApi } = await import('@/services/api')
      const result = await requestsApi.aiClassify(requestId)
      const matchedRequest = (requests || []).find((item) => item.id === requestId) || null
      setAiResult(result)
      setAiResultRequest(matchedRequest)
      await refetch()
      queryClient.invalidateQueries({ queryKey: ['responses'] })
      queryClient.invalidateQueries({ queryKey: ['requests'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
    } catch (error: any) {
      console.error('Failed to run AI classification:', error)
      setAiErrorRequestId(requestId)
      setAiErrorMessage(error.response?.data?.detail || 'AI classification failed.')
    } finally {
      setAiProcessingRequestId(null)
    }
  }

  // Get broker IDs that already have an active (pending or sent) request
  const activeRequests = (requests || []).filter(r => r.status === 'pending' || r.status === 'sent')
  const existingBrokerIds = new Set(activeRequests.map(r => r.broker_id))

  // Get unique brokers from email scans that don't have requests yet
  const brokersWithoutRequests = brokerEmails
    ?.filter((email): email is EmailScan & { broker_id: string } =>
      email.broker_id !== null && !existingBrokerIds.has(email.broker_id)
    )
    .reduce((acc, email) => {
      if (!acc.find(e => e.broker_id === email.broker_id)) {
        acc.push(email)
      }
      return acc
    }, [] as (EmailScan & { broker_id: string })[])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <AlertTriangle className="h-12 w-12 mb-4" />
        <p>Failed to load requests</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Deletion Requests</h1>
          <p className="text-muted-foreground">
            Manage your data deletion requests
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={handleScanResponses}
            disabled={scanResponses.isPending}
          >
            {scanResponses.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Scan for Responses
              </>
            )}
          </Button>
        </div>
      </div>

      {createWarning && (
        <div className="rounded-md border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-900">
          {createWarning}
        </div>
      )}
      {scanSuccessMessage && (
        <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-900 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          {scanSuccessMessage}
        </div>
      )}
      {scanErrorMessage && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {scanErrorMessage}
        </div>
      )}

      {/* Create New Requests */}
      {brokersWithoutRequests && brokersWithoutRequests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Create New Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Found {brokersWithoutRequests.length} data broker(s) without deletion requests:
            </p>
            <div className="space-y-2">
              {brokersWithoutRequests.map((email) => (
                <div
                  key={email.broker_id}
                  className="flex items-center justify-between p-3 bg-muted rounded-lg"
                >
                  <div>
                    <p className="font-medium">{email.sender_email}</p>
                    <p className="text-xs text-muted-foreground">
                      Broker ID: {email.broker_id}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleCreateRequest(email.broker_id)}
                    disabled={creatingFor === email.broker_id}
                  >
                    {creatingFor === email.broker_id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Plus className="h-4 w-4 mr-1" />
                        Create Request
                      </>
                    )}
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Existing Requests */}
      {requests && requests.length > 0 ? (
        <div className="space-y-4">
          {requests.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              brokerName={brokerMap.get(request.broker_id) || 'Unknown Broker'}
              onPreview={() => setPreviewRequest(request)}
              onSendEmail={handleSendEmail}
              isSending={sendingRequestId === request.id}
              onAiAssist={handleAiAssist}
              isAiProcessing={aiProcessingRequestId === request.id}
              aiErrorMessage={aiErrorRequestId === request.id ? aiErrorMessage : null}
              responses={responsesByRequest.get(request.id) || []}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No deletion requests yet. Scan your emails to find data brokers.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Email Preview Dialog */}
      <EmailPreviewDialog
        request={previewRequest}
        responses={previewResponses}
        onClose={() => setPreviewRequest(null)}
      />

      <AiResultDialog
        result={aiResult}
        request={aiResultRequest}
        brokerName={aiResultRequest ? brokerMap.get(aiResultRequest.broker_id) || 'Unknown Broker' : undefined}
        onClose={() => {
          setAiResult(null)
          setAiResultRequest(null)
        }}
      />

      {/* Permission Error Dialog */}
      {permissionError && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="max-w-md">
            <CardHeader>
              <CardTitle>Additional Permission Required</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                To send deletion requests, we need permission to send emails on your behalf.
                You'll be redirected to grant this permission.
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={() => {
                    // Trigger re-authorization
                    window.location.href = '/login'
                  }}
                  className="flex-1"
                >
                  Re-authorize
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setPermissionError(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

type TimelineTone = 'default' | 'success' | 'warning' | 'danger'

interface TimelineEvent {
  id: string
  label: string
  timestamp: string
  description?: string | null
  icon: ComponentType<{ className?: string }>
  tone?: TimelineTone
  actionLabel?: string
  onAction?: () => void
}

const responseTypeConfig: Record<BrokerResponseType, { label: string; color: string; bg: string; icon: any }> = {
  confirmation: { label: 'Confirmation', color: 'text-green-600', bg: 'bg-green-50', icon: CheckCircle },
  rejection: { label: 'Rejection', color: 'text-red-600', bg: 'bg-red-50', icon: XCircle },
  acknowledgment: { label: 'Acknowledged', color: 'text-blue-600', bg: 'bg-blue-50', icon: Clock },
  request_info: { label: 'Info Requested', color: 'text-yellow-600', bg: 'bg-yellow-50', icon: AlertCircle },
  unknown: { label: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-50', icon: HelpCircle },
}

function RequestCard({
  request,
  brokerName,
  onPreview,
  onSendEmail,
  isSending,
  onAiAssist,
  isAiProcessing,
  aiErrorMessage,
  responses
}: {
  request: DeletionRequest
  brokerName: string
  onPreview: () => void
  onSendEmail: (requestId: string) => void
  isSending: boolean
  onAiAssist: (requestId: string) => void
  isAiProcessing: boolean
  aiErrorMessage: string | null
  responses: BrokerResponse[]
}) {
  const classifyResponse = useClassifyResponse()
  const statusConfig = {
    pending: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-500/10', label: 'Pending' },
    sent: { icon: Mail, color: 'text-blue-500', bg: 'bg-blue-500/10', label: 'Sent' },
    response_received: { icon: MessageSquare, color: 'text-cyan-600', bg: 'bg-cyan-500/10', label: 'Response received' },
    confirmed: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-500/10', label: 'Confirmed' },
    rejected: { icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-500/10', label: 'Rejected' },
  }

  const latestResponse = useMemo(() => {
    if (responses.length === 0) return null
    return responses.reduce((latest, current) => {
      const latestDate = new Date(latest.received_date || latest.created_at).getTime()
      const currentDate = new Date(current.received_date || current.created_at).getTime()
      return currentDate > latestDate ? current : latest
    })
  }, [responses])
  const hasResponse = Boolean(latestResponse)
  const statusKey = hasResponse && request.status === 'sent' ? 'response_received' : request.status
  const config = statusConfig[statusKey as keyof typeof statusConfig] || statusConfig.pending
  const StatusIcon = config.icon
  const responseConfig = latestResponse ? responseTypeConfig[latestResponse.response_type] : null
  const [responseEdits, setResponseEdits] = useState<Record<string, BrokerResponseType>>({})
  const [saveStatuses, setSaveStatuses] = useState<Record<string, 'idle' | 'saving' | 'saved' | 'error'>>({})

  const [showTimeline, setShowTimeline] = useState(false)
  const nextRetryDate = request.next_retry_at ? new Date(request.next_retry_at) : null
  const isRateLimited = nextRetryDate ? nextRetryDate.getTime() > Date.now() : false

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatRelative = (date: Date) => {
    const diffMs = date.getTime() - Date.now()
    if (diffMs <= 0) return 'now'
    const diffMinutes = Math.round(diffMs / 60000)
    if (diffMinutes < 60) return `${diffMinutes} min`
    const diffHours = Math.round(diffMinutes / 60)
    if (diffHours < 24) return `${diffHours} hr`
    const diffDays = Math.round(diffHours / 24)
    return `${diffDays} day${diffDays > 1 ? 's' : ''}`
  }

  const timelineEvents = useMemo<TimelineEvent[]>(() => {
    const events: TimelineEvent[] = [
      {
        id: `${request.id}-created`,
        label: 'Request created',
        timestamp: request.created_at,
        description: `Email drafted for ${brokerName}`,
        icon: FileText,
      },
    ]

    events.push({
      id: `${request.id}-preview`,
      label: 'Email preview ready',
      timestamp: request.created_at,
      icon: Eye,
      actionLabel: 'Open preview',
      onAction: onPreview,
    })

    if (request.sent_at) {
      events.push({
        id: `${request.id}-sent`,
        label: 'Email sent',
        timestamp: request.sent_at,
        icon: Send,
        tone: 'success',
      })
    }

    if (request.confirmed_at) {
      events.push({
        id: `${request.id}-confirmed`,
        label: 'Request confirmed',
        timestamp: request.confirmed_at,
        icon: CheckCircle,
        tone: 'success',
      })
    }

    if (request.rejected_at) {
      events.push({
        id: `${request.id}-rejected`,
        label: 'Request rejected',
        timestamp: request.rejected_at,
        icon: AlertTriangle,
        tone: 'danger',
      })
    }

    if (request.last_send_error) {
      events.push({
        id: `${request.id}-error`,
        label: 'Send attempt failed',
        timestamp: request.updated_at,
        icon: AlertTriangle,
        tone: 'warning',
        description: request.last_send_error,
      })
    }

    responses.forEach((response) => {
      if (!response.received_date && !response.created_at) {
        return
      }
      events.push({
        id: response.id,
        label: `Response: ${response.response_type.replace('_', ' ')}`,
        timestamp: response.received_date || response.created_at,
        icon: MessageSquare,
        description: response.subject || response.sender_email,
      })
    })

    return events
      .filter((event) => Boolean(event.timestamp))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  }, [request, brokerName, responses, onPreview])

  const getToneClasses = (tone: TimelineTone = 'default') => {
    switch (tone) {
      case 'success':
        return 'bg-green-100 text-green-700'
      case 'warning':
        return 'bg-yellow-100 text-yellow-700'
      case 'danger':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-muted text-foreground'
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={config.bg}>
                <StatusIcon className={`h-3 w-3 mr-1 ${config.color}`} />
                {config.label}
              </Badge>
              {latestResponse && responseConfig && (
                <>
                  <Badge variant="outline" className={`${responseConfig.bg} ${responseConfig.color}`}>
                    Response: {responseConfig.label}
                  </Badge>
                  {latestResponse.confidence_score !== null && (
                    <Badge variant="secondary">
                      {Math.round(latestResponse.confidence_score * 100)}% confidence
                    </Badge>
                  )}
                </>
              )}
            </div>
            <p className="text-sm font-medium">
              {brokerName}
            </p>
            {request.sent_at && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Calendar className="h-3 w-3" />
                <span>Sent: {formatDate(request.sent_at)}</span>
              </div>
            )}
            {latestResponse && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <MessageSquare className="h-3 w-3" />
                <span>
                  Response received: {formatDate(latestResponse.received_date || latestResponse.created_at) || 'Unknown'}
                </span>
              </div>
            )}
            {!request.sent_at && (
              <p className="text-xs text-muted-foreground">
                Created: {new Date(request.created_at).toLocaleDateString()}
              </p>
            )}
          </div>

          <div className="flex-1 min-w-[240px]">
            <div className="flex flex-wrap gap-2 justify-start md:justify-end">
              <Button variant="outline" size="sm" onClick={onPreview}>
                <Eye className="h-4 w-4 mr-1" />
                Preview
              </Button>

              {request.status === 'pending' && (
                <Button
                  size="sm"
                  onClick={() => onSendEmail(request.id)}
                  disabled={isSending || isRateLimited}
                  variant={isRateLimited ? 'secondary' : 'default'}
                >
                  {isSending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      Sending...
                    </>
                  ) : isRateLimited ? (
                    <>
                      <Clock className="h-4 w-4 mr-1" />
                      Retry later
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-1" />
                      Send Email
                    </>
                  )}
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => onAiAssist(request.id)}
                disabled={isAiProcessing}
              >
                {isAiProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    AI running...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-1" />
                    AI Assist
                  </>
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowTimeline((prev) => !prev)}
              >
                <History className="h-4 w-4 mr-1" />
                {showTimeline ? 'Hide history' : 'View history'}
              </Button>
            </div>

            {isRateLimited && nextRetryDate && (
              <p className="text-xs text-muted-foreground mt-2">
                Gmail rate limit active. Try again {formatRelative(nextRetryDate)} ({nextRetryDate.toLocaleTimeString()}).
              </p>
            )}
            {request.last_send_error && (
              <p className="text-xs text-destructive mt-1">{request.last_send_error}</p>
            )}
            {aiErrorMessage && (
              <p className="text-xs text-destructive mt-1">{aiErrorMessage}</p>
            )}

            {showTimeline && (
              <div className="mt-4 border-t pt-4 space-y-4">
                {timelineEvents.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No activity recorded yet.</p>
                ) : (
                  timelineEvents.map((event) => {
                    const ToneIcon = event.icon
                    return (
                      <div key={event.id} className="flex items-start gap-3">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center ${getToneClasses(event.tone)}`}>
                          <ToneIcon className="h-4 w-4" />
                        </div>
                        <div className="flex-1 text-sm">
                          <div className="flex items-center justify-between gap-2">
                            <p className="font-medium">{event.label}</p>
                            <span className="text-xs text-muted-foreground">
                              {formatDate(event.timestamp) || 'Unknown'}
                            </span>
                          </div>
                          {event.description && (
                            <p className="text-xs text-muted-foreground mt-0.5">{event.description}</p>
                          )}
                          {event.actionLabel && event.onAction && (
                            <Button variant="link" className="px-0 text-xs" onClick={event.onAction}>
                              {event.actionLabel}
                            </Button>
                          )}
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            )}

            {responses.length > 0 && (
              <div className="mt-4 border-t pt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">Responses ({responses.length})</p>
                </div>
                <div className="space-y-3">
                  {responses.map((response) => {
                    const config = responseTypeConfig[response.response_type] || responseTypeConfig.unknown
                    const Icon = config.icon
                    const responseDate = formatDate(response.received_date || response.created_at) || 'Unknown'
                    const responseSelection = responseEdits[response.id] || response.response_type
                    const saveStatus = saveStatuses[response.id] || 'idle'
                    return (
                      <div key={response.id} className="rounded-lg border bg-muted/40 p-4 space-y-3">
                        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <Badge variant="outline" className={`${config.bg} ${config.color}`}>
                                <Icon className="h-3 w-3 mr-1" />
                                {config.label}
                              </Badge>
                              {response.confidence_score !== null && (
                                <Badge variant="secondary">
                                  {Math.round(response.confidence_score * 100)}% confidence
                                </Badge>
                              )}
                              {response.matched_by && (
                                <Badge variant="outline">
                                  Matched: {response.matched_by}
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              From: {response.sender_email}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Received: {responseDate}
                            </p>
                            {response.subject && (
                              <p className="text-sm font-medium">{response.subject}</p>
                            )}
                          </div>
                          <div className="space-y-2 md:text-right">
                            <p className="text-xs text-muted-foreground">
                              Manual classification (reclassify only)
                            </p>
                            <div className="flex flex-wrap gap-2 md:justify-end">
                              <select
                                value={responseSelection}
                                onChange={(event) =>
                                  setResponseEdits((prev) => ({
                                    ...prev,
                                    [response.id]: event.target.value as BrokerResponseType,
                                  }))
                                }
                                className="text-xs border rounded-md px-2 py-1.5 bg-background"
                              >
                                <option value="confirmation">Confirmation</option>
                                <option value="rejection">Rejection</option>
                                <option value="acknowledgment">Acknowledged</option>
                                <option value="request_info">Info Requested</option>
                                <option value="unknown">Unknown</option>
                              </select>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={async () => {
                                  try {
                                    setSaveStatuses((prev) => ({
                                      ...prev,
                                      [response.id]: 'saving',
                                    }))
                                    await classifyResponse.mutateAsync({
                                      responseId: response.id,
                                      responseType: responseSelection,
                                    })
                                    setSaveStatuses((prev) => ({
                                      ...prev,
                                      [response.id]: 'saved',
                                    }))
                                    setTimeout(() => {
                                      setSaveStatuses((prev) => ({
                                        ...prev,
                                        [response.id]: 'idle',
                                      }))
                                    }, 2000)
                                  } catch (saveError) {
                                    console.error('Failed to classify response', saveError)
                                    setSaveStatuses((prev) => ({
                                      ...prev,
                                      [response.id]: 'error',
                                    }))
                                    setTimeout(() => {
                                      setSaveStatuses((prev) => ({
                                        ...prev,
                                        [response.id]: 'idle',
                                      }))
                                    }, 3000)
                                  }
                                }}
                                disabled={saveStatus === 'saving'}
                              >
                                {saveStatus === 'saving' ? 'Saving...' : 'Save'}
                              </Button>
                              {saveStatus === 'saved' && (
                                <span className="text-xs text-muted-foreground">Saved</span>
                              )}
                              {saveStatus === 'error' && (
                                <span className="text-xs text-muted-foreground">Save failed</span>
                              )}
                            </div>
                          </div>
                        </div>
                        {response.body_text && (
                          <div className="rounded-md bg-background/80 p-3 text-xs text-muted-foreground">
                            {response.body_text}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
