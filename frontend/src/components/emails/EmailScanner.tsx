import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { tasksApi } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { TaskStatus } from '@/types'
import { Loader2, Play, CheckCircle, XCircle, Mail, RotateCw, Clock } from 'lucide-react'

export function EmailScanner() {
  const { userId, user } = useAuthStore()
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [isStarting, setIsStarting] = useState(false)
  const [daysBack, setDaysBack] = useState(30)
  const [maxEmails, setMaxEmails] = useState(300)

  // Poll for task status
  useEffect(() => {
    if (!taskId) return

    const pollStatus = async () => {
      try {
        const status = await tasksApi.getTaskStatus(taskId)
        setTaskStatus(status)

        // Stop polling if task is complete or failed
        if (status.state === 'SUCCESS' || status.state === 'FAILURE') {
          return
        }
      } catch (error) {
        console.error('Failed to fetch task status:', error)
      }
    }

    // Poll immediately
    pollStatus()

    // Then poll every 2 seconds
    const interval = setInterval(pollStatus, 2000)

    return () => clearInterval(interval)
  }, [taskId])

  const handleStartScan = async () => {
    if (!userId) return

    setIsStarting(true)
    try {
      const response = await tasksApi.startScan(userId, daysBack, maxEmails)
      setTaskId(response.task_id)
      setTaskStatus(null)
    } catch (error) {
      console.error('Failed to start scan:', error)
    } finally {
      setIsStarting(false)
    }
  }

  const getProgress = () => {
    if (!taskStatus?.info) return 0
    const { current, total } = taskStatus.info
    if (!total || current === undefined) return 0
    return Math.round((current / total) * 100)
  }

  const isScanning = taskStatus?.state === 'PROGRESS' || taskStatus?.state === 'PENDING' || taskStatus?.state === 'STARTED'
  const isComplete = taskStatus?.state === 'SUCCESS'
  const isFailed = taskStatus?.state === 'FAILURE'

  const getLastScanText = () => {
    if (!user?.last_scan_at) return 'Never scanned'

    const lastScan = new Date(user.last_scan_at)
    const now = new Date()
    const diffMs = now.getTime() - lastScan.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffHours < 1) return 'Less than an hour ago'
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

    return lastScan.toLocaleDateString()
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Email Scanner</h1>
          <p className="text-muted-foreground">
            Scan your inbox for data broker communications
          </p>
        </div>
        {user?.last_scan_at && (
          <Badge variant="outline" className="flex items-center gap-2">
            <Clock className="h-3 w-3" />
            Last scan: {getLastScanText()}
          </Badge>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Scan Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Scan Configuration</CardTitle>
            <CardDescription>
              Configure how many emails to scan
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Days to look back</label>
              <input
                type="number"
                value={daysBack}
                onChange={(e) => setDaysBack(Number(e.target.value))}
                min={1}
                max={365}
                disabled={isScanning}
                className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <p className="text-xs text-muted-foreground mt-1">
                How far back to search in your inbox
              </p>
            </div>

            <div>
              <label className="text-sm font-medium">Maximum emails</label>
              <input
                type="number"
                value={maxEmails}
                onChange={(e) => setMaxEmails(Number(e.target.value))}
                min={10}
                max={1000}
                disabled={isScanning}
                className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Maximum number of emails to process
              </p>
            </div>

            <Button
              onClick={handleStartScan}
              disabled={isStarting || isScanning || !userId}
              className="w-full"
            >
              {isStarting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Starting...
                </>
              ) : isScanning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Start Scan
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Scan Status */}
        <Card>
          <CardHeader>
            <CardTitle>Scan Status</CardTitle>
            <CardDescription>
              {taskId ? `Task ID: ${taskId.slice(0, 8)}...` : 'No active scan'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!taskId && !taskStatus && (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <Mail className="h-12 w-12 mb-4" />
                <p>Start a scan to detect data broker emails</p>
              </div>
            )}

            {isScanning && (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span>{taskStatus?.info?.status || 'Processing...'}</span>
                  <span>{getProgress()}%</span>
                </div>
                <Progress value={getProgress()} />
                <p className="text-xs text-muted-foreground text-center">
                  {taskStatus?.info?.current || 0} of {taskStatus?.info?.total || maxEmails} emails processed
                </p>
              </div>
            )}

            {isComplete && taskStatus?.result && (
              <div className="space-y-4">
                <div className="flex items-center text-green-600">
                  <CheckCircle className="h-5 w-5 mr-2" />
                  <span className="font-medium">Scan Complete</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold">{taskStatus.result.total_scanned}</p>
                    <p className="text-xs text-muted-foreground">Emails Scanned</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-orange-600">{taskStatus.result.broker_emails_found}</p>
                    <p className="text-xs text-muted-foreground">Broker Emails Found</p>
                  </div>
                </div>
                <Button
                  onClick={handleStartScan}
                  variant="outline"
                  className="w-full"
                  disabled={isStarting}
                >
                  <RotateCw className="mr-2 h-4 w-4" />
                  Rescan Inbox
                </Button>
              </div>
            )}

            {isFailed && (
              <div className="space-y-4">
                <div className="flex items-center text-red-600">
                  <XCircle className="h-5 w-5 mr-2" />
                  <span className="font-medium">Scan Failed</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {taskStatus?.info?.error || 'An error occurred during scanning'}
                </p>
                <Button onClick={handleStartScan} variant="outline" className="w-full">
                  Retry Scan
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
