import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { requestsApi } from '@/services/api'
import { BrokerResponse, BrokerResponseType, DeletionRequest, GeneratedEmail } from '@/types'
import { X, Copy, Check, Loader2, Mail } from 'lucide-react'

interface EmailPreviewDialogProps {
  request: DeletionRequest | null
  responses: BrokerResponse[]
  onSend?: () => Promise<void> | void
  isSending?: boolean
  sendDisabled?: boolean
  sendDisabledReason?: string
  onClose: () => void
}

const requestStatusConfig = {
  pending: { label: 'Pending', color: 'text-yellow-600', bg: 'bg-yellow-50' },
  sent: { label: 'Sent', color: 'text-blue-600', bg: 'bg-blue-50' },
  confirmed: { label: 'Confirmed', color: 'text-green-600', bg: 'bg-green-50' },
  rejected: { label: 'Rejected', color: 'text-red-600', bg: 'bg-red-50' },
}

const responseTypeConfig: Record<BrokerResponseType, { label: string; color: string; bg: string }> = {
  confirmation: { label: 'Confirmation', color: 'text-green-600', bg: 'bg-green-50' },
  rejection: { label: 'Rejection', color: 'text-red-600', bg: 'bg-red-50' },
  acknowledgment: { label: 'Acknowledged', color: 'text-blue-600', bg: 'bg-blue-50' },
  request_info: { label: 'Info Requested', color: 'text-yellow-600', bg: 'bg-yellow-50' },
  unknown: { label: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-50' },
}

export function EmailPreviewDialog({
  request,
  responses,
  onSend,
  isSending = false,
  sendDisabled = false,
  sendDisabledReason,
  onClose,
}: EmailPreviewDialogProps) {
  const [email, setEmail] = useState<GeneratedEmail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState<'subject' | 'body' | null>(null)

  useEffect(() => {
    if (request) {
      loadEmailPreview()
    } else {
      setEmail(null)
      setError(null)
    }
  }, [request])

  const loadEmailPreview = async () => {
    if (!request) return

    setIsLoading(true)
    setError(null)

    try {
      const preview = await requestsApi.previewEmail(request.id)
      setEmail(preview)
    } catch (err) {
      setError('Failed to generate email preview')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = async (type: 'subject' | 'body') => {
    if (!email) return

    const text = type === 'subject' ? email.subject : email.body
    await navigator.clipboard.writeText(text)
    setCopied(type)
    setTimeout(() => setCopied(null), 2000)
  }

  if (!request) return null
  const statusStyle = requestStatusConfig[request.status] || requestStatusConfig.pending

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

  const threadMessages = [...responses]
    .sort((a, b) => {
      const dateA = new Date(a.received_date || a.created_at).getTime()
      const dateB = new Date(b.received_date || b.created_at).getTime()
      return dateA - dateB
    })

  const requestSubject = email?.subject || request.generated_email_subject || '(No subject)'
  const requestBody = email?.body || request.generated_email_body || 'No message content available.'
  const requestTo = email?.to_email || 'Unknown recipient'
  const requestTimestamp = request.sent_at || request.created_at
  const requestMessageStatus = request.sent_at ? 'Sent' : 'Draft'
  const requestMessageStyle = request.sent_at
    ? { label: 'Sent', color: 'text-blue-600', bg: 'bg-blue-50' }
    : { label: 'Draft', color: 'text-yellow-600', bg: 'bg-yellow-50' }
  const canSend = Boolean(onSend) && request.status === 'pending'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <Card className="relative z-10 w-full max-w-2xl mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center gap-3">
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Email Preview
            </CardTitle>
            <Badge variant="outline" className={`${statusStyle.bg} ${statusStyle.color}`}>
              {statusStyle.label}
            </Badge>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>

        <CardContent className="overflow-y-auto flex-1">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && (
            <div className="text-center py-12 text-red-500">
              {error}
            </div>
          )}

          {!isLoading && (
            <div className="space-y-6">
              {/* To */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">To:</label>
                <p className="mt-1 text-sm">{email?.to_email || requestTo}</p>
              </div>

              {/* Subject */}
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-muted-foreground">Subject:</label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopy('subject')}
                    disabled={!email}
                  >
                    {copied === 'subject' ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="mt-1 text-sm font-medium">{requestSubject}</p>
              </div>

              {/* Body */}
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-muted-foreground">Body:</label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopy('body')}
                    disabled={!email}
                  >
                    {copied === 'body' ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <div className="mt-2 p-4 bg-muted rounded-lg">
                  <pre className="text-sm whitespace-pre-wrap font-sans">
                    {requestBody}
                  </pre>
                </div>
              </div>

              <div className="border-t pt-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold">Thread timeline</h3>
                  <span className="text-xs text-muted-foreground">
                    {threadMessages.length + 1} message{threadMessages.length + 1 === 1 ? '' : 's'}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="rounded-lg border bg-muted/40 p-4 space-y-3">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1">
                        <p className="text-sm font-semibold">Original request</p>
                        <p className="text-xs text-muted-foreground">
                          From: You · To: {requestTo}
                        </p>
                        <p className="text-sm font-medium">{requestSubject}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={`${requestMessageStyle.bg} ${requestMessageStyle.color}`}>
                          {requestMessageStatus}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(requestTimestamp) || 'Unknown'}
                        </span>
                      </div>
                    </div>
                    <div className="rounded-md bg-background p-3">
                      <pre className="text-xs whitespace-pre-wrap font-sans">
                        {requestBody}
                      </pre>
                    </div>
                  </div>

                  {threadMessages.length === 0 ? (
                    <p className="text-xs text-muted-foreground">
                      No responses yet. We'll show replies here as they arrive.
                    </p>
                  ) : (
                    threadMessages.map((response) => {
                      const responseStyle = responseTypeConfig[response.response_type] || responseTypeConfig.unknown
                      const responseTimestamp = response.received_date || response.created_at
                      return (
                        <div key={response.id} className="rounded-lg border bg-muted/40 p-4 space-y-3">
                          <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                            <div className="space-y-1">
                              <p className="text-sm font-semibold">Response from {response.sender_email}</p>
                              <p className="text-xs text-muted-foreground">
                                To: You
                              </p>
                              <p className="text-sm font-medium">
                                {response.subject || '(No subject)'}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className={`${responseStyle.bg} ${responseStyle.color}`}>
                                {responseStyle.label}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(responseTimestamp) || 'Unknown'}
                              </span>
                            </div>
                          </div>
                          <div className="rounded-md bg-background p-3">
                            <pre className="text-xs whitespace-pre-wrap font-sans">
                              {response.body_text || 'No message content available.'}
                            </pre>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={onClose}>
                  Close
                </Button>
                <Button
                  onClick={() => {
                    if (!email) return
                    window.open(
                      `mailto:${email.to_email}?subject=${encodeURIComponent(email.subject)}&body=${encodeURIComponent(email.body)}`,
                      '_blank'
                    )
                  }}
                  disabled={!email}
                >
                  <Mail className="h-4 w-4 mr-2" />
                  Open in Email Client
                </Button>
                {canSend && (
                  <div className="flex flex-col items-end">
                    <Button
                      onClick={onSend}
                      disabled={isSending || sendDisabled}
                    >
                      {isSending ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Mail className="h-4 w-4 mr-2" />
                          Send Email
                        </>
                      )}
                    </Button>
                    {sendDisabledReason && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        {sendDisabledReason}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
