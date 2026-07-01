import { Link, Outlet, createRootRoute } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: RootComponent,
})

const navLinkClass =
  'text-muted-foreground transition-colors hover:text-foreground [&.active]:text-foreground'

function RootComponent() {
  return (
    <div className="min-h-svh bg-background text-foreground">
      <nav className="flex flex-wrap gap-4 border-b px-6 py-4 text-sm font-medium">
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
      </nav>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
