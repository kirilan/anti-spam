import { Link } from 'react-router-dom'
import { useLogin } from '@/hooks/useAuth'
import { useAuthStore } from '@/stores/authStore'
import { Button, buttonVariants } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const supportEmail = import.meta.env.VITE_SUPPORT_EMAIL || 'support@example.com'

export function PublicHome() {
  const { login } = useLogin()
  const { isAuthenticated } = useAuthStore()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-full bg-secondary">
              <img src="/logo-mark.png" alt="OpenShred logo" className="h-full w-full object-cover" />
            </div>
            <div>
              <p className="text-base font-semibold">OpenShred</p>
              <p className="text-xs text-muted-foreground">Data deletion assistant</p>
            </div>
          </div>
          <nav className="flex items-center gap-3 text-sm text-muted-foreground">
            <Link className="hover:text-foreground" to="/privacy">
              Privacy
            </Link>
            <Link className="hover:text-foreground" to="/terms">
              Terms
            </Link>
            <a
              className="hover:text-foreground"
              href="https://github.com/kirilan/OpenShred"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
            </a>
            {isAuthenticated ? (
              <Link className={buttonVariants({ variant: 'secondary', size: 'sm' })} to="/dashboard">
                Open dashboard
              </Link>
            ) : null}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-6 py-12">
        <section className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
          <div className="space-y-5">
            <Badge variant="secondary" className="w-fit">
              Open source • Free to use
            </Badge>
            <h1 className="text-4xl font-semibold leading-tight md:text-5xl">
              OpenShred is an open-source data deletion assistant for Gmail.
            </h1>
            <p className="text-lg text-muted-foreground">
              It connects to Gmail, identifies broker emails, and drafts GDPR/CCPA deletion requests.
              The service is free of charge and provided as-is, without guarantees.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              {isAuthenticated ? (
                <Link className={buttonVariants({ size: 'lg' })} to="/dashboard">
                  Open dashboard
                </Link>
              ) : (
                <Button onClick={login} size="lg" className="shadow-sm">
                  Sign in with Google
                </Button>
              )}
              <p className="text-xs text-muted-foreground">
                {isAuthenticated ? (
                  'You are signed in. Continue to your dashboard to get started.'
                ) : (
                  <>
                    By continuing, you agree to our{' '}
                    <Link className="text-foreground hover:underline" to="/terms">
                      Terms
                    </Link>{' '}
                    and{' '}
                    <Link className="text-foreground hover:underline" to="/privacy">
                      Privacy Policy
                    </Link>
                    .
                  </>
                )}
              </p>
            </div>
            <div className="rounded-lg border bg-card p-4 text-sm text-muted-foreground">
              <p className="font-semibold text-foreground">About OpenShred</p>
              <p className="mt-2">
                This project is fully open source and free to use. If you want maximum privacy, run
                your own copy locally and keep everything on your machine.
              </p>
              <a
                className="mt-3 inline-flex text-foreground hover:underline"
                href="https://github.com/kirilan/OpenShred"
                target="_blank"
                rel="noreferrer"
              >
                Explore the GitHub repository
              </a>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Quick usage guide</CardTitle>
              <CardDescription>What to expect in your first session.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ol className="space-y-3 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                    1
                  </span>
                  <span>Sign in with Google and connect your Gmail inbox.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                    2
                  </span>
                  <span>Review deletion requests before they are sent.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                    3
                  </span>
                  <span>Track responses and follow-up tasks in the dashboard.</span>
                </li>
              </ol>
              <p className="text-xs text-muted-foreground">
                Access can be revoked at any time from your Google account settings.
              </p>
            </CardContent>
          </Card>
        </section>

        <section className="mt-12 grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Email scanning</CardTitle>
              <CardDescription>Finds broker messages and groups them by request thread.</CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Request drafting</CardTitle>
              <CardDescription>Generates deletion emails you can edit before sending.</CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Progress tracking</CardTitle>
              <CardDescription>Monitors responses and deadlines for follow-ups.</CardDescription>
            </CardHeader>
          </Card>
        </section>
      </main>

      <footer className="border-t bg-muted/20">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-6 py-6 text-xs text-muted-foreground md:flex-row md:items-center md:justify-between">
          <p>OpenShred helps individuals manage data broker deletion requests.</p>
          <p>
            Support:{" "}
            <a className="text-foreground hover:underline" href={`mailto:${supportEmail}`}>
              {supportEmail}
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
