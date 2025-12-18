import { useState } from 'react'
import { useAdminUsers, useUpdateUserRole, useRevokeTokens } from '@/hooks/useAdmin'
import { useAuthStore } from '@/stores/authStore'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, ShieldAlert, UserCheck, UserX } from 'lucide-react'
import type { User } from '@/types'

export function UserManagement() {
  const { user } = useAuthStore()
  const { data: users, isLoading, isError } = useAdminUsers()
  const updateUserRole = useUpdateUserRole()
  const revokeTokens = useRevokeTokens()
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  if (!user?.is_admin) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Admin Access Required</CardTitle>
          <CardDescription>You need admin privileges to view this page.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-2 text-sm text-muted-foreground">
          <ShieldAlert className="h-4 w-4" />
          Contact an administrator if you believe this is an error.
        </CardContent>
      </Card>
    )
  }

  const handleToggleRole = async (target: User) => {
    setStatusMessage(null)
    setErrorMessage(null)
    try {
      await updateUserRole.mutateAsync({ userId: target.id, isAdmin: !target.is_admin })
      setStatusMessage(
        `${target.email} is now ${!target.is_admin ? 'an admin' : 'a standard user'}.`
      )
    } catch (err) {
      const detail = (err as any)?.response?.data?.detail || 'Unable to update role.'
      setErrorMessage(detail)
    }
  }

  const handleRevoke = async (target: User) => {
    setStatusMessage(null)
    setErrorMessage(null)
    try {
      await revokeTokens.mutateAsync(target.id)
      setStatusMessage(`Revoked Gmail tokens for ${target.email}.`)
    } catch (err) {
      const detail = (err as any)?.response?.data?.detail || 'Unable to revoke tokens.'
      setErrorMessage(detail)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Users</h1>
        <p className="text-muted-foreground">
          Manage admin roles and reset Gmail integrations for any account.
        </p>
      </div>

      {(statusMessage || errorMessage) && (
        <div
          className={`rounded-md border px-3 py-2 text-sm ${
            errorMessage
              ? 'border-red-200 bg-red-50 text-red-600'
              : 'border-green-200 bg-green-50 text-green-600'
          }`}
        >
          {errorMessage || statusMessage}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>User Directory</CardTitle>
          <CardDescription>Only trusted accounts should have admin privileges.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : isError ? (
            <p className="text-sm text-destructive">
              Failed to load users. Check your connection and try again.
            </p>
          ) : users && users.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-muted-foreground">
                    <th className="pb-2 font-medium">Email</th>
                    <th className="pb-2 font-medium">Role</th>
                    <th className="pb-2 font-medium">Last Scan</th>
                    <th className="pb-2 font-medium">Created</th>
                    <th className="pb-2 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-t">
                      <td className="py-3">
                        <div className="font-medium">{u.email}</div>
                        <div className="text-xs text-muted-foreground">{u.google_id}</div>
                      </td>
                      <td className="py-3">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs ${
                            u.is_admin
                              ? 'bg-green-100 text-green-700'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {u.is_admin ? 'Admin' : 'User'}
                        </span>
                      </td>
                      <td className="py-3 text-muted-foreground">
                        {u.last_scan_at ? new Date(u.last_scan_at).toLocaleString() : 'Never'}
                      </td>
                      <td className="py-3 text-muted-foreground">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRevoke(u)}
                              disabled={revokeTokens.isPending}
                          >
                            {revokeTokens.isPending ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <>
                                <UserX className="mr-1 h-4 w-4" />
                                Revoke Gmail
                              </>
                            )}
                          </Button>
                          <Button
                            variant={u.is_admin ? 'secondary' : 'default'}
                            size="sm"
                            onClick={() => handleToggleRole(u)}
                            disabled={updateUserRole.isPending}
                          >
                            {updateUserRole.isPending ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : u.is_admin ? (
                              <>
                                <UserX className="mr-1 h-4 w-4" />
                                Remove Admin
                              </>
                            ) : (
                              <>
                                <UserCheck className="mr-1 h-4 w-4" />
                                Make Admin
                              </>
                            )}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No users found.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
