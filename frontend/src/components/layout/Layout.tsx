import { useEffect, useState } from 'react'
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
  PanelLeftClose,
  PanelLeftOpen,
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
  const storageKey = 'sidebar-collapsed'
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window === 'undefined') {
      return false
    }
    const stored = window.localStorage.getItem(storageKey)
    if (stored !== null) {
      return stored === 'true'
    }
    return window.matchMedia('(max-width: 1024px)').matches
  })

  useEffect(() => {
    window.localStorage.setItem(storageKey, String(isCollapsed))
  }, [isCollapsed])

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-40 h-screen border-r bg-card transition-[width] ${
          isCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div
            className={`flex h-16 items-center justify-between border-b ${
              isCollapsed ? 'px-0' : 'px-4'
            }`}
          >
            <div className="flex items-center gap-2 overflow-hidden">
              <img
                src="/logo-mark.png"
                alt="OpenShred logo"
                className="h-8 w-8 shrink-0"
              />
              {!isCollapsed && <span className="text-lg font-semibold">OpenShred</span>}
            </div>
            <Button
              variant="ghost"
              size="icon"
              className={isCollapsed ? 'h-8 w-8 shrink-0' : 'shrink-0'}
              onClick={() => setIsCollapsed((prev) => !prev)}
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isCollapsed ? (
                <PanelLeftOpen className="h-4 w-4" />
              ) : (
                <PanelLeftClose className="h-4 w-4" />
              )}
            </Button>
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
                  title={item.label}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  } ${isCollapsed ? 'justify-center px-2' : ''}`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {!isCollapsed && item.label}
                </Link>
              )
            })}
          </nav>

          {/* User section */}
          <div className="border-t p-4 space-y-3">
            {!isCollapsed && (
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm flex-1 min-w-0">
                  <p className="font-medium truncate">{user?.email || 'Not logged in'}</p>
                </div>
              </div>
            )}
            <Button
              variant="outline"
              size={isCollapsed ? 'icon' : 'sm'}
              className="w-full"
              onClick={logout}
              title="Logout"
            >
              <LogOut className={isCollapsed ? 'h-4 w-4' : 'mr-2 h-4 w-4'} />
              {!isCollapsed && 'Logout'}
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className={`min-h-screen transition-all ${isCollapsed ? 'ml-16' : 'ml-64'}`}>
        <div className="p-8">
          <RateLimitNotice />
          <Outlet />
        </div>
      </main>
    </div>
  )
}
