import { Outlet, createRootRoute } from '@tanstack/react-router'
import { ClerkLoaded, ClerkLoading, Show, SignIn } from '@clerk/react'

export const Route = createRootRoute({
  component: RootComponent,
})

// The authentication boundary, and nothing else: everything that assumes a
// signed-in user lives under the _authenticated layout, so a future public
// route (a shared report, an OAuth callback) can sit outside it.
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
          <Outlet />
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
