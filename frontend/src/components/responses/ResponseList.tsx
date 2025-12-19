import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useResponses, useScanResponses, useClassifyResponse } from '@/hooks/useResponses'
import type { BrokerResponse, BrokerResponseType } from '@/types'
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  HelpCircle,
  Loader2,
  RefreshCw,
  Mail,
  CheckCircle2
} from 'lucide-react'

const responseTypeConfig: Record<BrokerResponseType, { icon: any; color: string; bg: string; label: string }> = {
  confirmation: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', label: 'Confirmation' },
  rejection: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', label: 'Rejection' },
  acknowledgment: { icon: Clock, color: 'text-blue-600', bg: 'bg-blue-50', label: 'Acknowledged' },
  request_info: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-50', label: 'Info Requested' },
  unknown: { icon: HelpCircle, color: 'text-gray-600', bg: 'bg-gray-50', label: 'Unknown' }
}

export function ResponseList() {
  const [filterType, setFilterType] = useState<BrokerResponseType | 'all'>('all')
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [showSuccess, setShowSuccess] = useState(false)
  const { data: responses, isLoading, error } = useResponses()
  const scanResponses = useScanResponses()

  // Set initial last updated time when responses load
  useEffect(() => {
    if (responses && responses.length > 0 && !lastUpdated) {
      setLastUpdated(new Date())
    }
  }, [responses, lastUpdated])

  const handleScan = async () => {
    try {
      await scanResponses.mutateAsync(7)
      setLastUpdated(new Date())
      setShowSuccess(true)
      setTimeout(() => setShowSuccess(false), 3000) // Hide after 3 seconds
    } catch (error) {
      console.error('Scan failed:', error)
    }
  }

  const formatLastUpdated = (date: Date | null) => {
    if (!date) return ''
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSecs = Math.floor(diffMs / 1000)
    const diffMins = Math.floor(diffSecs / 60)

    if (diffSecs < 10) return 'Just now'
    if (diffSecs < 60) return `${diffSecs} seconds ago`
    if (diffMins === 1) return '1 minute ago'
    if (diffMins < 60) return `${diffMins} minutes ago`
    return date.toLocaleTimeString()
  }

  const filteredResponses = responses?.filter(
    r => filterType === 'all' || r.response_type === filterType
  )

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
        <XCircle className="h-12 w-12 mb-4" />
        <p>Failed to load responses</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Broker Responses</h1>
        <p className="text-muted-foreground">
          View and manage responses from data brokers
        </p>
      </div>

      {/* Actions Bar */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              onClick={handleScan}
              disabled={scanResponses.isPending}
              variant="default"
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

            {lastUpdated && !scanResponses.isPending && (
              <span className="text-sm text-muted-foreground">
                Last updated: {formatLastUpdated(lastUpdated)}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Filter:</span>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as BrokerResponseType | 'all')}
              className="text-sm border rounded-md px-3 py-1.5 bg-background"
            >
              <option value="all">All Types</option>
              <option value="confirmation">Confirmations</option>
              <option value="rejection">Rejections</option>
              <option value="acknowledgment">Acknowledged</option>
              <option value="request_info">Info Requested</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
        </div>

        {/* Success Message */}
        {showSuccess && (
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-md animate-in fade-in slide-in-from-top-2 duration-300">
            <CheckCircle2 className="h-5 w-5" />
            <div>
              <p className="font-medium">Scan complete!</p>
              <p className="text-sm text-green-700">
                {responses?.length || 0} response{responses?.length !== 1 ? 's' : ''} found
              </p>
            </div>
          </div>
        )}

        {/* Scanning Animation */}
        {scanResponses.isPending && (
          <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-md animate-pulse">
            <Loader2 className="h-5 w-5 animate-spin" />
            <div>
              <p className="font-medium">Scanning your inbox...</p>
              <p className="text-sm text-blue-700">Looking for broker responses in the last 7 days</p>
            </div>
          </div>
        )}
      </div>

      {/* Response Cards */}
      {filteredResponses && filteredResponses.length > 0 ? (
        <div className="space-y-4">
          {filteredResponses.map((response) => (
            <ResponseCard key={response.id} response={response} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Mail className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">
              No responses found. Scan for responses to check if brokers have replied.
            </p>
            <Button onClick={handleScan} disabled={scanResponses.isPending}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Scan Now
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function ResponseCard({ response }: { response: BrokerResponse }) {
  const [expanded, setExpanded] = useState(false)
  const [selectedType, setSelectedType] = useState<BrokerResponseType>(response.response_type)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const classifyResponse = useClassifyResponse()
  const config = responseTypeConfig[response.response_type] || responseTypeConfig.unknown
  const Icon = config.icon

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown date'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    return date.toLocaleDateString()
  }

  const handleSave = async () => {
    try {
      setSaveMessage(null)
      await classifyResponse.mutateAsync({
        responseId: response.id,
        responseType: selectedType,
        deletionRequestId: response.deletion_request_id,
      })
      setSaveMessage('Classification saved')
      setTimeout(() => setSaveMessage(null), 2500)
    } catch (err) {
      console.error('Failed to classify response', err)
      setSaveMessage('Save failed')
      setTimeout(() => setSaveMessage(null), 3000)
    }
  }

  // Keep local selection in sync when data refreshes
  useEffect(() => {
    setSelectedType(response.response_type)
  }, [response.response_type])

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
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
            <div className="space-y-1">
              <p className="text-sm">
                <span className="font-medium">From:</span> {response.sender_email}
              </p>
              {response.subject && (
                <p className="text-sm">
                  <span className="font-medium">Subject:</span> {response.subject}
                </p>
              )}
              <p className="text-sm text-muted-foreground">
                <span className="font-medium">Received:</span> {formatDate(response.received_date)}
              </p>
              {response.deletion_request_id && (
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium">Linked to Request:</span> {response.deletion_request_id.substring(0, 8)}...
                </p>
              )}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0 border-t">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium">Manual classification</p>
            <p className="text-xs text-muted-foreground">
              Confirmation/Rejection will update the linked request status.
            </p>
          </div>
          <div className="flex flex-col md:flex-row gap-2 md:items-center">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as BrokerResponseType)}
              className="text-sm border rounded-md px-3 py-2 bg-background"
            >
              <option value="confirmation">Confirmation</option>
              <option value="rejection">Rejection</option>
              <option value="acknowledgment">Acknowledged</option>
              <option value="request_info">Info Requested</option>
              <option value="unknown">Unknown</option>
            </select>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={classifyResponse.isPending}
            >
              {classifyResponse.isPending ? 'Saving...' : 'Save'}
            </Button>
            {saveMessage && (
              <span className="text-xs text-muted-foreground">{saveMessage}</span>
            )}
          </div>
        </div>
      </CardContent>

      {response.body_text && (
        <CardContent className="pt-0">
          <div className="space-y-2">
            <div className="text-sm text-muted-foreground bg-muted/50 rounded-md p-3 border">
              <p className={expanded ? '' : 'line-clamp-3'}>
                {response.body_text}
              </p>
            </div>
            {response.body_text.length > 200 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(!expanded)}
              >
                {expanded ? 'Show less' : 'Show more'}
              </Button>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
