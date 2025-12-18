import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useBrokers, useSyncBrokers } from '@/hooks/useBrokers'
import { useCreateRequest } from '@/hooks/useRequests'
import { Broker } from '@/types'
import { Database, Globe, Mail, Loader2, AlertTriangle, FileText, RefreshCw } from 'lucide-react'

export function BrokerList() {
  const { data: brokers, isLoading, error } = useBrokers()
  const syncBrokers = useSyncBrokers()
  const [syncMessage, setSyncMessage] = useState<string | null>(null)
  const [syncError, setSyncError] = useState<string | null>(null)

  const handleSyncBrokers = async () => {
    setSyncMessage(null)
    setSyncError(null)
    try {
      const result = await syncBrokers.mutateAsync()
      const defaultMessage =
        result.brokers_added > 0
          ? `${result.brokers_added} brokers added (${result.total_brokers} total)`
          : `Database already up to date (${result.total_brokers} total)`
      setSyncMessage(result.message || defaultMessage)
    } catch (err) {
      console.error('Failed to sync brokers:', err)
      setSyncError('Failed to sync brokers. Please try again.')
    }
  }

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
        <p>Failed to load brokers</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Brokers</h1>
          <p className="text-muted-foreground">
            {brokers?.length || 0} known data brokers in database
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={handleSyncBrokers}
          disabled={syncBrokers.isPending}
        >
          {syncBrokers.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Syncing...
            </>
          ) : (
            <>
              <RefreshCw className="mr-2 h-4 w-4" />
              Sync Brokers
            </>
          )}
        </Button>
      </div>

      {(syncMessage || syncError) && (
        <div
          className={`text-sm rounded-md border px-3 py-2 ${
            syncError ? 'text-red-500 border-red-200 bg-red-50' : 'text-green-600 border-green-200 bg-green-50'
          }`}
        >
          {syncError || syncMessage}
        </div>
      )}

      {brokers && brokers.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {brokers.map((broker) => (
            <BrokerCard key={broker.id} broker={broker} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center space-y-4 py-12 text-center">
            <Database className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No data brokers in the database yet. Sync from the broker directory to load the defaults.
            </p>
            <Button onClick={handleSyncBrokers} disabled={syncBrokers.isPending}>
              {syncBrokers.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Syncing...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Sync Brokers
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function BrokerCard({ broker }: { broker: Broker }) {
  const navigate = useNavigate()
  const createRequest = useCreateRequest()
  const [isCreating, setIsCreating] = useState(false)

  const handleCreateRequest = async () => {
    setIsCreating(true)
    try {
      await createRequest.mutateAsync(broker.id)
      navigate('/requests')
    } catch (error) {
      console.error('Failed to create request:', error)
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg">{broker.name}</CardTitle>
          <Badge variant={broker.supports_automated_removal ? 'default' : 'secondary'}>
            {broker.supports_automated_removal ? 'Auto Removal' : 'Manual'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {broker.website && (
          <div className="flex items-center text-sm text-muted-foreground">
            <Globe className="h-4 w-4 mr-2" />
            <a
              href={broker.website}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline truncate"
            >
              {broker.website.replace(/^https?:\/\//, '')}
            </a>
          </div>
        )}
        {broker.privacy_policy_url && (
          <div className="flex items-center text-sm text-muted-foreground">
            <Mail className="h-4 w-4 mr-2" />
            <a
              href={broker.privacy_policy_url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              Privacy Policy
            </a>
          </div>
        )}
        {broker.email_patterns && broker.email_patterns.length > 0 && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground mb-1">Email Patterns:</p>
            <div className="flex flex-wrap gap-1">
              {broker.email_patterns.slice(0, 3).map((pattern, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {pattern}
                </Badge>
              ))}
              {broker.email_patterns.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{broker.email_patterns.length - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}
        <div className="pt-3 border-t">
          <Button
            className="w-full"
            onClick={handleCreateRequest}
            disabled={isCreating}
          >
            {isCreating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <FileText className="mr-2 h-4 w-4" />
                Create Deletion Request
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
