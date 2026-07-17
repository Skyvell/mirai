import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { currentUserOptions } from '@/client/@tanstack/react-query.gen'
import { Page } from '@/components/page'
import { apiErrorMessage } from '@/lib/api'

export const Route = createFileRoute('/')({
  component: OverviewComponent,
})

function OverviewComponent() {
  const me = useQuery(currentUserOptions())

  return (
    <Page
      title="Overview"
      description="Personal health summary, key changes since last test, risk signals, active interventions, and recommended follow-ups."
    >
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
    </Page>
  )
}
