import { Link, Outlet, createFileRoute, useNavigate } from '@tanstack/react-router'
import { UserButton } from '@clerk/react'
import { useQuery } from '@tanstack/react-query'
import { Settings } from 'lucide-react'
import { currentUserOptions } from '@/client/@tanstack/react-query.gen'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { AddDataDialog } from '@/features/sources/add-data-dialog'
import { Onboarding } from '@/features/profile/components/onboarding'

export const Route = createFileRoute('/_authenticated')({
  component: AuthenticatedLayout,
})

const navLinkClass =
  'text-muted-foreground transition-colors hover:text-foreground [&.active]:text-foreground'

// Gate every route below this one on a complete health profile: sex and date of
// birth are required before any biomarker range can be shown.
function AuthenticatedLayout() {
  const me = useQuery(currentUserOptions())

  if (me.isPending) {
    return (
      <div className="grid min-h-svh place-items-center text-sm text-muted-foreground">
        Loading…
      </div>
    )
  }

  if (me.isError) {
    return (
      <div className="grid min-h-svh place-items-center p-6">
        <div className="w-full max-w-md">
          <ApiErrorAlert error={me.error} />
        </div>
      </div>
    )
  }

  if (me.data.sex == null || me.data.date_of_birth == null) {
    return <Onboarding current={me.data} />
  }

  return <AppShell />
}

function AppShell() {
  const navigate = useNavigate()

  return (
    <>
      <nav className="flex flex-wrap items-center gap-4 border-b px-6 py-4 text-sm font-medium">
        <Link to="/" activeOptions={{ exact: true }} className={navLinkClass}>
          Overview
        </Link>
        <Link to="/biomarkers" className={navLinkClass}>
          Biomarkers
        </Link>
        <Link to="/wearables" className={navLinkClass}>
          Wearables
        </Link>
        <Link to="/omics" className={navLinkClass}>
          Omics
        </Link>
        <Link to="/insights" className={navLinkClass}>
          Insights
        </Link>
        <Link to="/interventions" className={navLinkClass}>
          Interventions
        </Link>
        <div className="ml-auto flex items-center gap-3">
          <AddDataDialog />
          <UserButton>
            <UserButton.MenuItems>
              <UserButton.Action
                label="Settings"
                labelIcon={<Settings className="size-4" />}
                onClick={() => navigate({ to: '/settings' })}
              />
            </UserButton.MenuItems>
          </UserButton>
        </div>
      </nav>
      <main className="p-6">
        <Outlet />
      </main>
    </>
  )
}
