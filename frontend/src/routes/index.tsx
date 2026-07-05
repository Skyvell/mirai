import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useAuth } from '@clerk/react'
import { getMe } from '@/lib/api'

export const Route = createFileRoute('/')({
  component: OverviewComponent,
})

function OverviewComponent() {
  const { getToken } = useAuth()
  const [backendUserId, setBackendUserId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Fire once per mount — Overview only renders while signed in, so it remounts
  // on the next sign-in. The cancelled flag guards the StrictMode double-mount.
  useEffect(() => {
    let cancelled = false
    getToken()
      .then((token) => (token ? getMe(token) : Promise.reject(new Error('No token'))))
      .then((me) => !cancelled && setBackendUserId(me.user_id))
      .catch((err) => !cancelled && setError(String(err)))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Overview</h1>
      <p className="text-muted-foreground">
        Personal health summary, key changes since last test, risk signals,
        active interventions, and recommended follow-ups.
      </p>
      <p className="text-sm text-muted-foreground">
        Backend auth check:{' '}
        {error ? (
          <span className="text-destructive">{error}</span>
        ) : backendUserId ? (
          <span className="font-mono text-foreground">{backendUserId}</span>
        ) : (
          '…'
        )}
      </p>
    </div>
  )
}
