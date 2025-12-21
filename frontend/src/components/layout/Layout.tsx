import { Link, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { useLogout } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { RateLimitNotice } from './RateLimitNotice'
import {
  LayoutDashboard,
  Database,
  FileText,
  LogOut,
  ScanSearch,
  BarChart3,
  List,
  Settings,
} from 'lucide-react'

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/scan', label: 'Scan Emails', icon: ScanSearch },
  { href: '/brokers', label: 'Data Brokers', icon: Database },
  { href: '/requests', label: 'Deletion Requests', icon: FileText },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/activity', label: 'Activity Log', icon: List },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Layout() {
  const location = useLocation()
  const { user } = useAuthStore()
  const { logout } = useLogout()

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-card">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-2 border-b px-6">
            <img src="/logo-mark.png" alt="OpenShred logo" className="h-8 w-8" />
            <span className="text-lg font-semibold">OpenShred</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          {/* User section */}
          <div className="border-t p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm flex-1 min-w-0">
                <p className="font-medium truncate">{user?.email || 'Not logged in'}</p>
              </div>
            </div>
            <Button variant="outline" size="sm" className="w-full" onClick={logout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 min-h-screen">
        <div className="p-8">
          <RateLimitNotice />
          <Outlet />
        </div>
      </main>
    </div>
  )
}
