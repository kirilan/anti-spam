import { useState } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  useAnalytics,
  useBrokerRanking,
  useTimeline,
  useResponseDistribution,
} from '@/hooks/useAnalytics'
import { useRequests } from '@/hooks/useRequests'
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import {
  TrendingUp,
  Clock,
  CheckCircle,
  Send,
  Loader2,
  BarChart3,
  Award,
} from 'lucide-react'

const COLORS = ['#22c55e', '#ef4444', '#3b82f6', '#eab308', '#8b5cf6']

export function AnalyticsDashboard() {
  const [timelineDays, setTimelineDays] = useState(30)
  const { data: stats, isLoading: statsLoading } = useAnalytics()
  const { data: brokerRanking, isLoading: rankingLoading } = useBrokerRanking()
  const { data: timeline, isLoading: timelineLoading } = useTimeline(timelineDays)
  const { data: distribution, isLoading: distributionLoading } = useResponseDistribution()
  const { data: requests } = useRequests()
  const requestBrokerIds = new Set(requests?.map((request) => request.broker_id) || [])

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
        <p className="text-muted-foreground">
          Track your deletion request success and broker compliance
        </p>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Total Requests"
            value={stats.total_requests}
            icon={Send}
            description="Deletion requests created"
          />
          <StatsCard
            title="Success Rate"
            value={`${Math.round(stats.success_rate)}%`}
            icon={TrendingUp}
            description="Confirmed deletions"
            trend={stats.success_rate >= 70 ? 'positive' : 'neutral'}
          />
          <StatsCard
            title="Confirmations"
            value={stats.confirmed_deletions}
            icon={CheckCircle}
            description={`Out of ${stats.total_requests} request${stats.total_requests === 1 ? '' : 's'}`}
          />
          <StatsCard
            title="Avg Response Time"
            value={stats.avg_response_time_days ? `${stats.avg_response_time_days.toFixed(1)}d` : 'N/A'}
            icon={Clock}
            description="Days to broker response"
          />
        </div>
      )}

      {/* Timeline Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="text-lg font-semibold">Request Timeline</h3>
              <p className="text-sm text-muted-foreground">
                Requests sent vs confirmations received over time
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant={timelineDays === 7 ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimelineDays(7)}
              >
                7d
              </Button>
              <Button
                variant={timelineDays === 30 ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimelineDays(30)}
              >
                30d
              </Button>
              <Button
                variant={timelineDays === 90 ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimelineDays(90)}
              >
                90d
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {timelineLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : timeline && timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="requests_sent"
                  stroke="#3b82f6"
                  name="Requests Sent"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="confirmations_received"
                  stroke="#22c55e"
                  name="Confirmations"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
              <p>No timeline data available</p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Broker Compliance Ranking */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Award className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Broker Compliance Ranking</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              Top brokers by success rate and response time
            </p>
          </CardHeader>
          <CardContent>
            {rankingLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : brokerRanking && brokerRanking.length > 0 ? (
              <div className="space-y-3">
                {brokerRanking.slice(0, 10).map((broker, index) => {
                  const hasRequest = requestBrokerIds.has(broker.broker_id)
                  return (
                    <div key={broker.broker_id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-primary/10 text-primary font-semibold">
                        {index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium truncate">{broker.broker_name}</p>
                          <Badge variant={hasRequest ? 'default' : 'outline'} className="text-[10px]">
                            {hasRequest ? 'Request created' : 'No request yet'}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {broker.confirmations}/{broker.total_requests} requests
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={broker.success_rate >= 80 ? 'default' : 'secondary'}>
                          {Math.round(broker.success_rate)}%
                        </Badge>
                        {broker.avg_response_time_days !== null && (
                          <div className="flex items-center gap-1 text-sm text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            {broker.avg_response_time_days.toFixed(1)}d
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 text-muted-foreground">
                <p>No broker ranking data available</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Response Distribution */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-semibold">Response Type Distribution</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              Breakdown of broker response types
            </p>
          </CardHeader>
          <CardContent>
            {distributionLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : distribution && distribution.length > 0 ? (
              <div className="space-y-4">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={distribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ response_type, percentage }) => `${response_type}: ${Math.round(percentage)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {distribution.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2">
                  {distribution.map((item, index) => (
                    <div key={item.response_type} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="capitalize">{item.response_type.replace('_', ' ')}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{item.count}</span>
                        <span className="text-muted-foreground">({Math.round(item.percentage)}%)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 text-muted-foreground">
                <p>No response distribution data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

interface StatsCardProps {
  title: string
  value: string | number
  icon: React.ComponentType<{ className?: string }>
  description?: string
  trend?: 'positive' | 'negative' | 'neutral'
}

function StatsCard({ title, value, icon: Icon, description, trend = 'neutral' }: StatsCardProps) {
  const trendColor = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-muted-foreground',
  }[trend]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <h3 className="text-sm font-medium">{title}</h3>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${trendColor}`}>{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  )
}
