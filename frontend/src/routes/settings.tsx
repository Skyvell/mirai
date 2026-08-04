import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'

import { currentUserOptions } from '@/client/@tanstack/react-query.gen'
import { Page } from '@/components/page'
import { ProfileForm } from '@/components/profile-form'
import { ApiErrorAlert } from '@/components/api-error-alert'

export const Route = createFileRoute('/settings')({
  component: SettingsPage,
})

function SettingsPage() {
  const me = useQuery(currentUserOptions())

  return (
    <Page title="Settings">
      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-medium">Health profile</h2>
        <p className="text-sm text-muted-foreground">
          Sets the reference ranges your biomarkers are compared against.
        </p>

        <div className="mt-2 max-w-md">
          {me.isError && <ApiErrorAlert error={me.error} />}
          {me.data && <ProfileForm current={me.data} submitLabel="Save changes" />}
        </div>
      </section>
    </Page>
  )
}
