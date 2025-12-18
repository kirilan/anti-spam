import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useEmailScans } from '@/hooks/useEmails'
import { useRequests } from '@/hooks/useRequests'
import { useBrokers } from '@/hooks/useBrokers'
import { useResponses } from '@/hooks/useResponses'
import { useAnalytics } from '@/hooks/useAnalytics'
import { useTaskHealth } from '@/hooks/useTasks'
import { Mail, Database, FileText, CheckCircle, Clock, TrendingUp, MessageSquare, ScanSearch, BarChart3, Server, RefreshCw, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

const responseTypeConfig: Record<string, { color: string; bg: string }> = {
  confirmation: { color: 'text-green-600', bg: 'bg-green-50' },
  rejection: { color: 'text-red-600', bg: 'bg-red-50' },
  acknowledgment: { color: 'text-blue-600', bg: 'bg-blue-50' },
  request_info: { color: 'text-yellow-600', bg: 'bg-yellow-50' },
  unknown: { color: 'text-gray-600', bg: 'bg-gray-50' }
}

export function Dashboard() {
  const { user } = useAuthStore()
  const { data: allScans } = useEmailScans(false)
  const { data: brokerScans } = useEmailScans(true)
  const { data: requests } = useRequests()
  const { data: brokers } = useBrokers()
  const { data: responses } = useResponses()
  const { data: analytics } = useAnalytics()
  const { data: taskHealth, isLoading: taskHealthLoading, refetch: refetchTaskHealth } = useTaskHealth()

  const pendingRequests = requests?.filter((r) => r.status === 'pending').length || 0
  const sentRequests = requests?.filter((r) => r.status === 'sent').length || 0
  const confirmedRequests = requests?.filter((r) => r.status === 'confirmed').length || 0
  const recentResponses = responses?.slice(0, 3) || []
  const requestBrokerIds = new Set(requests?.map((request) => request.broker_id) || [])

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your data deletion activities
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Emails Scanned</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allScans?.length || 0}</div>
            <p className="text-xs text-muted-foreground">
              {brokerScans?.length || 0} broker emails found
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Known Brokers</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{brokers?.length || 0}</div>
            <p className="text-xs text-muted-foreground">In database</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Deletion Requests</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{requests?.length || 0}</div>
            <p className="text-xs text-muted-foreground">Total created</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {analytics?.success_rate ? `${Math.round(analytics.success_rate)}%` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {confirmedRequests} of {sentRequests} sent
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Request Status Breakdown */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingRequests}</div>
            <p className="text-xs text-muted-foreground">Awaiting action</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sent</CardTitle>
            <Mail className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sentRequests}</div>
            <p className="text-xs text-muted-foreground">Awaiting response</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Confirmed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{confirmedRequests}</div>
            <p className="text-xs text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Recent Responses */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Broker Responses</CardTitle>
            <Link to="/responses">
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recentResponses.length > 0 ? (
              <div className="space-y-4">
                {recentResponses.map((response) => {
                  const config = responseTypeConfig[response.response_type] || responseTypeConfig.unknown
                  return (
                    <div
                      key={response.id}
                      className="flex items-start justify-between border-b pb-4 last:border-0 last:pb-0"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className={`${config.bg} ${config.color}`}>
                            {response.response_type.replace('_', ' ')}
                          </Badge>
                          {response.confidence_score && (
                            <span className="text-xs text-muted-foreground">
                              {Math.round(response.confidence_score * 100)}%
                            </span>
                          )}
                        </div>
                        <p className="text-sm font-medium truncate">{response.sender_email}</p>
                        <p className="text-xs text-muted-foreground truncate">{response.subject}</p>
                      </div>
                      <div className="text-right text-xs text-muted-foreground ml-4">
                        {response.received_date
                          ? new Date(response.received_date).toLocaleDateString()
                          : 'Unknown'}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <MessageSquare className="h-12 w-12 mb-2" />
                <p className="text-sm">No responses yet</p>
                <Link to="/responses" className="mt-2">
                  <Button variant="outline" size="sm">
                    Scan for Responses
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link to="/scan" className="block">
              <Button className="w-full justify-start" variant="outline">
                <ScanSearch className="mr-2 h-4 w-4" />
                Scan Inbox for Brokers
              </Button>
            </Link>
            <Link to="/responses" className="block">
              <Button className="w-full justify-start" variant="outline">
                <MessageSquare className="mr-2 h-4 w-4" />
                Check Broker Responses
              </Button>
            </Link>
            <Link to="/analytics" className="block">
              <Button className="w-full justify-start" variant="outline">
                <BarChart3 className="mr-2 h-4 w-4" />
                View Analytics
              </Button>
            </Link>
            <Link to="/requests" className="block">
              <Button className="w-full justify-start" variant="outline">
                <FileText className="mr-2 h-4 w-4" />
                Manage Deletion Requests
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Task Queue Health */}
      {user?.is_admin && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-primary" />
              <CardTitle>Task Queue Status</CardTitle>
            </div>
            <Button variant="ghost" size="sm" onClick={() => refetchTaskHealth()}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {taskHealthLoading ? (
              <div className="flex items-center justify-center py-6 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            ) : taskHealth ? (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-3 text-center">
                  <div>
                    <p className="text-sm text-muted-foreground">Workers Online</p>
                    <p className="text-2xl font-bold">{taskHealth.workers_online}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Active Tasks</p>
                    <p className="text-2xl font-bold">{taskHealth.total_active_tasks}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Queued/Scheduled</p>
                    <p className="text-2xl font-bold">{taskHealth.total_queued_tasks}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  {taskHealth.workers.length > 0 ? (
                    taskHealth.workers.map((worker) => (
                      <div key={worker.name} className="rounded-lg border p-3">
                        <div className="flex items-center justify-between">
                          <p className="font-medium">{worker.name}</p>
                          <Badge variant={worker.status === 'online' ? 'default' : 'destructive'}>
                            {worker.status}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          Active: {worker.active_tasks} | Queued: {worker.queued_tasks} | Scheduled: {worker.scheduled_tasks}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground text-center">No workers detected.</p>
                  )}
                </div>
                <p className="text-xs text-muted-foreground text-right">
                  Updated {new Date(taskHealth.last_updated).toLocaleTimeString()}
                </p>
              </div>
            ) : (
              <p className="text-center text-sm text-muted-foreground py-4">
                Unable to fetch task queue status.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Broker Emails */}
      {brokerScans && brokerScans.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Broker Emails</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {brokerScans.slice(0, 5).map((scan) => (
                <div
                  key={scan.id}
                  className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
                >
                  <div>
                    <p className="font-medium">{scan.sender_email}</p>
                    <p className="text-sm text-muted-foreground">{scan.subject}</p>
                    {scan.broker_id && (
                      <Badge
                        variant={requestBrokerIds.has(scan.broker_id) ? 'default' : 'outline'}
                        className="mt-2 text-xs"
                      >
                        {requestBrokerIds.has(scan.broker_id) ? 'Request created' : 'No request yet'}
                      </Badge>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm">
                      {scan.confidence_score
                        ? `${Math.round(scan.confidence_score * 100)}% match`
                        : 'Unknown'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {scan.received_date
                        ? new Date(scan.received_date).toLocaleDateString()
                        : 'Unknown date'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
