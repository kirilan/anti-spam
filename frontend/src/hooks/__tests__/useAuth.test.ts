import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useAuthStatus, useLogin, useLogout } from '../useAuth'
import { createQueryWrapper } from '@/test/utils'
import { useAuthStore } from '@/stores/authStore'

// Mock the auth store
vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(),
}))

// Mock the API
vi.mock('@/services/api', () => ({
  authApi: {
    getStatus: vi.fn(),
    login: vi.fn(),
  },
}))

describe('useAuth hooks', () => {
  const mockSetUser = vi.fn()
  const mockClearAuth = vi.fn()
  const mockSetLoading = vi.fn()
  const mockSetToken = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    ;(useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      token: 'test-token',
      setUser: mockSetUser,
      clearAuth: mockClearAuth,
      setLoading: mockSetLoading,
      setToken: mockSetToken,
    })
  })

  describe('useAuthStatus', () => {
    it('should not fetch when no token is present', async () => {
      (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        token: null,
        setUser: mockSetUser,
        clearAuth: mockClearAuth,
        setLoading: mockSetLoading,
        setToken: mockSetToken,
      })

      const { result } = renderHook(() => useAuthStatus(), {
        wrapper: createQueryWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isFetching).toBe(false)
      })

      expect(mockSetLoading).toHaveBeenCalledWith(false)
    })

    it('should clear auth on error', async () => {
      const { authApi } = await import('@/services/api')
      ;(authApi.getStatus as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Unauthorized')
      )

      const { result } = renderHook(() => useAuthStatus(), {
        wrapper: createQueryWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(mockClearAuth).toHaveBeenCalled()
    })
  })

  describe('useLogin', () => {
    it('should store state and redirect to authorization URL', async () => {
      const { authApi } = await import('@/services/api')
      const mockAuthUrl = 'https://accounts.google.com/oauth'
      ;(authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        authorization_url: mockAuthUrl,
        state: 'test-state-123',
      })

      // Mock window.location
      const originalLocation = window.location
      delete (window as { location?: Location }).location
      window.location = { href: '' } as Location

      const { result } = renderHook(() => useLogin())

      await result.current.login()

      expect(sessionStorage.getItem('oauth_state')).toBe('test-state-123')
      expect(window.location.href).toBe(mockAuthUrl)

      // Restore window.location
      window.location = originalLocation
    })
  })

  describe('useLogout', () => {
    it('should clear auth and session storage', () => {
      sessionStorage.setItem('oauth_state', 'some-state')

      const { result } = renderHook(() => useLogout())

      result.current.logout()

      expect(mockClearAuth).toHaveBeenCalled()
      expect(sessionStorage.getItem('oauth_state')).toBeNull()
    })
  })
})
