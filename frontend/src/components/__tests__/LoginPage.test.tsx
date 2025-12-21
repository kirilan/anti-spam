import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginPage } from '../auth/LoginPage'

// Mock the useLogin hook
const mockLogin = vi.fn()
vi.mock('@/hooks/useAuth', () => ({
  useLogin: () => ({ login: mockLogin }),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    mockLogin.mockClear()
  })

  it('should render the login page with branding', () => {
    render(<LoginPage />)

    expect(screen.getByText('OpenShred')).toBeInTheDocument()
    expect(
      screen.getByText(/automatically find data brokers/i)
    ).toBeInTheDocument()
  })

  it('should render the logo image', () => {
    render(<LoginPage />)

    const logo = screen.getByAltText('OpenShred logo')
    expect(logo).toBeInTheDocument()
    expect(logo).toHaveAttribute('src', '/logo-mark.png')
  })

  it('should render the Google sign-in button', () => {
    render(<LoginPage />)

    const signInButton = screen.getByRole('button', { name: /sign in with google/i })
    expect(signInButton).toBeInTheDocument()
  })

  it('should call login when sign-in button is clicked', async () => {
    const user = userEvent.setup()

    render(<LoginPage />)

    const signInButton = screen.getByRole('button', { name: /sign in with google/i })
    await user.click(signInButton)

    expect(mockLogin).toHaveBeenCalledTimes(1)
  })

  it('should display help text about Gmail scanning', () => {
    render(<LoginPage />)

    expect(
      screen.getByText(/we'll scan your gmail for data broker emails/i)
    ).toBeInTheDocument()
  })

  it('should have proper styling classes for centered layout', () => {
    const { container } = render(<LoginPage />)

    // The outermost div has min-h-screen
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper).toHaveClass('min-h-screen')
  })
})
