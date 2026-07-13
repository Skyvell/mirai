import { Link, Outlet, createRootRoute } from '@tanstack/react-router'
import { ClerkLoaded, ClerkLoading, Show, SignIn, UserButton } from '@clerk/react'
import { AddDataDialog } from '@/components/add-data-dialog'

export const Route = createRootRoute({
  component: RootComponent,
})

const navLinkClass =
  'text-muted-foreground transition-colors hover:text-foreground [&.active]:text-foreground'

function RootComponent() {
  return (
    <div className="min-h-svh bg-background text-foreground">
      <ClerkLoading>
        <div className="grid min-h-svh place-items-center text-sm text-muted-foreground">
          Loading…
        </div>
      </ClerkLoading>
      <ClerkLoaded>
        <Show when="signed-in">
          <AppShell />
        </Show>
        <Show when="signed-out">
          <div className="grid min-h-svh place-items-center p-6">
            <SignIn />
          </div>
        </Show>
      </ClerkLoaded>
    </div>
  )
}

function AppShell() {
  return (
    <>
      <nav className="flex flex-wrap items-center gap-4 border-b px-6 py-4 text-sm font-medium">
        <Link to="/" activeOptions={{ exact: true }} className={navLinkClass}>
          Overview
        </Link>
        <Link to="/biomarkers" className={navLinkClass}>
          Biomarkers
        </Link>
        <Link to="/physiology" className={navLinkClass}>
          Physiology
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
          <UserButton />
        </div>
      </nav>
      <main className="p-6">
        <Outlet />
      </main>
    </>
  )
}
