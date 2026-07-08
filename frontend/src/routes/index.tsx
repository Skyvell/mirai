import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { currentUserOptions } from '@/client/@tanstack/react-query.gen'
import { apiErrorMessage } from '@/lib/api'

export const Route = createFileRoute('/')({
  component: OverviewComponent,
})

function OverviewComponent() {
  const me = useQuery(currentUserOptions())

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Overview</h1>
      <p className="text-muted-foreground">
        Personal health summary, key changes since last test, risk signals,
        active interventions, and recommended follow-ups.
      </p>
      <p className="text-sm text-muted-foreground">
        Backend auth check:{' '}
        {me.isError ? (
          <span className="text-destructive">{apiErrorMessage(me.error)}</span>
        ) : me.data ? (
          <span className="font-mono text-foreground">{me.data.user_id}</span>
        ) : (
          '…'
        )}
      </p>
    </div>
  )
}
