import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useRequests, useCreateRequest } from '@/hooks/useRequests'
import { useEmailScans } from '@/hooks/useEmails'
import { useBrokers } from '@/hooks/useBrokers'
import { DeletionRequest, EmailScan } from '@/types'
import { EmailPreviewDialog } from './EmailPreviewDialog'
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
  Calendar
} from 'lucide-react'

export function RequestList() {
  const { data: requests, isLoading, error, refetch } = useRequests()
  const { data: brokerEmails } = useEmailScans(true)
  const { data: brokers } = useBrokers()
  const createRequest = useCreateRequest()
  const [previewRequest, setPreviewRequest] = useState<DeletionRequest | null>(null)
  const [creatingFor, setCreatingFor] = useState<string | null>(null)
  const [sendingRequestId, setSendingRequestId] = useState<string | null>(null)
  const [permissionError, setPermissionError] = useState(false)

  // Create a map of broker IDs to broker names for quick lookup
  const brokerMap = new Map(brokers?.map(b => [b.id, b.name]) || [])

  const handleCreateRequest = async (brokerId: string) => {
    setCreatingFor(brokerId)
    try {
      await createRequest.mutateAsync(brokerId)
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
    } catch (error: any) {
      console.error('Failed to send email:', error)
      if (error.response?.status === 403 || error.response?.data?.detail?.includes('permission')) {
        setPermissionError(true)
      }
    } finally {
      setSendingRequestId(null)
    }
  }

  // Get broker IDs that already have requests
  const existingBrokerIds = new Set(requests?.map(r => r.broker_id) || [])

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
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Deletion Requests</h1>
        <p className="text-muted-foreground">
          Manage your data deletion requests
        </p>
      </div>

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
        onClose={() => setPreviewRequest(null)}
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

function RequestCard({
  request,
  brokerName,
  onPreview,
  onSendEmail,
  isSending
}: {
  request: DeletionRequest
  brokerName: string
  onPreview: () => void
  onSendEmail: (requestId: string) => void
  isSending: boolean
}) {
  const statusConfig = {
    pending: { icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
    sent: { icon: Mail, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    confirmed: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-500/10' },
  }

  const config = statusConfig[request.status as keyof typeof statusConfig] || statusConfig.pending
  const StatusIcon = config.icon

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

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className={config.bg}>
                <StatusIcon className={`h-3 w-3 mr-1 ${config.color}`} />
                {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
              </Badge>
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
            {!request.sent_at && (
              <p className="text-xs text-muted-foreground">
                Created: {new Date(request.created_at).toLocaleDateString()}
              </p>
            )}
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onPreview}>
              <Eye className="h-4 w-4 mr-1" />
              Preview
            </Button>

            {request.status === 'pending' && (
              <Button
                size="sm"
                onClick={() => onSendEmail(request.id)}
                disabled={isSending}
              >
                {isSending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-1" />
                    Send Email
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
