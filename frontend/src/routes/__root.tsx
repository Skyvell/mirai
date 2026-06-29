import { Link, Outlet, createRootRoute } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: RootComponent,
})

const navLinkClass =
  'text-muted-foreground transition-colors hover:text-foreground [&.active]:text-foreground'

function RootComponent() {
  return (
    <div className="min-h-svh bg-background text-foreground">
      <nav className="flex gap-4 border-b px-6 py-4 text-sm font-medium">
        <Link to="/" activeOptions={{ exact: true }} className={navLinkClass}>
          Home
        </Link>
        <Link to="/about" className={navLinkClass}>
          About
        </Link>
      </nav>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
