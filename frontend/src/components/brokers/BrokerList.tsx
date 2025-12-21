import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useBrokers, useSyncBrokers, useCreateBroker } from '@/hooks/useBrokers'
import { useCreateRequest, useRequests } from '@/hooks/useRequests'
import { Broker } from '@/types'
import {
  Database,
  Globe,
  Mail,
  Loader2,
  AlertTriangle,
  FileText,
  RefreshCw,
  Plus,
  ChevronUp,
} from 'lucide-react'

export function BrokerList() {
  const { data: brokers, isLoading, error } = useBrokers()
  const syncBrokers = useSyncBrokers()
  const { data: requests } = useRequests()
  const [syncMessage, setSyncMessage] = useState<string | null>(null)
  const [syncError, setSyncError] = useState<string | null>(null)
  const existingRequestBrokerIds = new Set(requests?.map((request) => request.broker_id) || [])

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

      <CreateBrokerForm />

      {brokers && brokers.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {brokers.map((broker) => (
            <BrokerCard
              key={broker.id}
              broker={broker}
              existingRequestBrokerIds={existingRequestBrokerIds}
            />
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

function CreateBrokerForm() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [formValues, setFormValues] = useState({
    name: '',
    domains: '',
    privacy_email: '',
    opt_out_url: '',
    category: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const createBroker = useCreateBroker()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)

    const trimmedName = formValues.name.trim()
    const domains = formValues.domains
      .split(',')
      .map((domain) => domain.trim())
      .filter(Boolean)

    if (!trimmedName || domains.length === 0) {
      setError('Name and at least one domain are required.')
      return
    }

    try {
      await createBroker.mutateAsync({
        name: trimmedName,
        domains,
        privacy_email: formValues.privacy_email.trim() || null,
        opt_out_url: formValues.opt_out_url.trim() || null,
        category: formValues.category.trim() || null,
      })
      setSuccess('Broker added successfully.')
      setFormValues({
        name: '',
        domains: '',
        privacy_email: '',
        opt_out_url: '',
        category: '',
      })
    } catch (err) {
      const detail =
        (err as any)?.response?.data?.detail || 'Failed to create broker. Please try again.'
      setError(detail)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div className="space-y-1">
          <CardTitle className="text-xl">Manual Broker Entry</CardTitle>
          <CardDescription>
            Add a single broker when you discover a new privacy contact.
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsExpanded((prev) => !prev)}
        >
          {isExpanded ? (
            <>
              <ChevronUp className="mr-2 h-4 w-4" />
              Hide Form
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" />
              Add Broker
            </>
          )}
        </Button>
      </CardHeader>
      {isExpanded && (
        <CardContent className="pt-0">
          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && (
              <div className="text-sm rounded-md border border-red-200 bg-red-50 px-3 py-2 text-red-600">
                {error}
              </div>
            )}
            {success && (
              <div className="text-sm rounded-md border border-green-200 bg-green-50 px-3 py-2 text-green-600">
                {success}
              </div>
            )}

            <div>
              <label className="text-sm font-medium">Broker name</label>
              <input
                type="text"
                value={formValues.name}
                onChange={(event) => setFormValues((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="Acme Privacy LLC"
                className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Domains</label>
              <textarea
                value={formValues.domains}
                onChange={(event) => setFormValues((prev) => ({ ...prev, domains: event.target.value }))}
                placeholder="acmeprivacy.com, privacy.acme.com"
                className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                rows={2}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Separate multiple domains with commas.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Privacy email</label>
                <input
                  type="email"
                  value={formValues.privacy_email}
                  onChange={(event) =>
                    setFormValues((prev) => ({ ...prev, privacy_email: event.target.value }))
                  }
                  placeholder="privacy@acmeprivacy.com"
                  className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Opt-out URL</label>
                <input
                  type="url"
                  value={formValues.opt_out_url}
                  onChange={(event) =>
                    setFormValues((prev) => ({ ...prev, opt_out_url: event.target.value }))
                  }
                  placeholder="https://acmeprivacy.com/opt-out"
                  className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">Category</label>
              <input
                type="text"
                value={formValues.category}
                onChange={(event) =>
                  setFormValues((prev) => ({ ...prev, category: event.target.value }))
                }
                placeholder="people_search"
                className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Optional grouping such as <code>people_search</code> or <code>aggregator</code>.
              </p>
            </div>

            <div className="flex justify-end">
              <Button type="submit" disabled={createBroker.isPending}>
                {createBroker.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    Save Broker
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      )}
    </Card>
  )
}

function BrokerCard({
  broker,
  existingRequestBrokerIds,
}: {
  broker: Broker
  existingRequestBrokerIds: Set<string>
}) {
  const navigate = useNavigate()
  const createRequest = useCreateRequest()
  const [isCreating, setIsCreating] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const alreadyRequested = existingRequestBrokerIds.has(broker.id)

  const handleCreateRequest = async () => {
    if (alreadyRequested) {
      return
    }

    setIsCreating(true)
    setErrorMessage(null)
    try {
      await createRequest.mutateAsync(broker.id)
      navigate('/requests')
    } catch (error) {
      console.error('Failed to create request:', error)
      const detail = (error as any)?.response?.data?.detail
      setErrorMessage(detail || 'Failed to create deletion request. Please try again.')
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-lg">{broker.name}</CardTitle>
            {alreadyRequested && (
              <Badge variant="secondary" className="mt-2 text-xs uppercase tracking-wide">
                Request already created
              </Badge>
            )}
            {broker.category && (
              <Badge variant="outline" className="mt-2 text-xs uppercase tracking-wide">
                {broker.category.replace('_', ' ')}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {broker.domains && broker.domains.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-1">Domains</p>
            <div className="flex flex-wrap gap-1">
              {broker.domains.slice(0, 4).map((domain, idx) => (
                <Badge key={`${broker.id}-domain-${idx}`} variant="outline" className="text-xs">
                  {domain}
                </Badge>
              ))}
              {broker.domains.length > 4 && (
                <Badge variant="outline" className="text-xs">
                  +{broker.domains.length - 4} more
                </Badge>
              )}
            </div>
          </div>
        )}
        {broker.privacy_email && (
          <div className="flex items-center text-sm text-muted-foreground">
            <Mail className="h-4 w-4 mr-2" />
            <span className="truncate">{broker.privacy_email}</span>
          </div>
        )}
        {broker.opt_out_url && (
          <div className="flex items-center text-sm text-muted-foreground">
            <Globe className="h-4 w-4 mr-2" />
            <a
              href={broker.opt_out_url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline truncate"
            >
              {broker.opt_out_url.replace(/^https?:\/\//, '')}
            </a>
          </div>
        )}
        <div className="pt-3 border-t">
          <Button
            className="w-full"
            onClick={handleCreateRequest}
            disabled={isCreating || alreadyRequested}
            variant={alreadyRequested ? 'secondary' : 'default'}
          >
            {isCreating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : alreadyRequested ? (
              <>
                <FileText className="mr-2 h-4 w-4" />
                Request already exists
              </>
            ) : (
              <>
                <FileText className="mr-2 h-4 w-4" />
                Create Deletion Request
              </>
            )}
          </Button>
          {errorMessage && (
            <p className="text-xs text-destructive mt-2">{errorMessage}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
