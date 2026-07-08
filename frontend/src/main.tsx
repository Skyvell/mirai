import { StrictMode, type ReactNode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClerkProvider, useAuth } from '@clerk/react'
import { setApiTokenGetter } from './lib/api'
import { routeTree } from './routeTree.gen'
import './index.css'

const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
  scrollRestoration: true,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

// Data changes only through explicit invalidation (e.g. after upload), so skip
// the default focus/remount refetching — each request costs a JWT verify + DB hit.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60_000, refetchOnWindowFocus: false },
  },
})

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!PUBLISHABLE_KEY) {
  throw new Error('Missing VITE_CLERK_PUBLISHABLE_KEY in .env.local')
}

// The generated client configures itself at creation (createClientConfig in
// lib/api.ts); only Clerk's render-scoped token getter must be injected here.
function ApiProvider({ children }: { children: ReactNode }) {
  const { getToken } = useAuth()
  setApiTokenGetter(getToken)
  return children
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
      <ApiProvider>
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      </ApiProvider>
    </ClerkProvider>
  </StrictMode>,
)
