import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { AuthGuard } from './components/auth/AuthGuard'
import { LoginPage } from './components/auth/LoginPage'
import { AuthCallback } from './components/auth/AuthCallback'
import { Dashboard } from './components/dashboard/Dashboard'
import { EmailScanner } from './components/emails/EmailScanner'
import { EmailList } from './components/emails/EmailList'
import { BrokerList } from './components/brokers/BrokerList'
import { RequestList } from './components/requests/RequestList'
import { ResponseList } from './components/responses/ResponseList'
import { AnalyticsDashboard } from './components/analytics/AnalyticsDashboard'
import { ActivityLog } from './components/activity/ActivityLog'
import { UserManagement } from './components/admin/UserManagement'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/oauth-callback" element={<AuthCallback />} />

        {/* Protected routes - AuthGuard wraps Layout */}
        <Route element={<AuthGuard />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/scan" element={<EmailScanner />} />
            <Route path="/emails" element={<EmailList />} />
            <Route path="/brokers" element={<BrokerList />} />
            <Route path="/requests" element={<RequestList />} />
            <Route path="/responses" element={<ResponseList />} />
            <Route path="/analytics" element={<AnalyticsDashboard />} />
            <Route path="/activity" element={<ActivityLog />} />
            <Route path="/admin/users" element={<UserManagement />} />
          </Route>
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
