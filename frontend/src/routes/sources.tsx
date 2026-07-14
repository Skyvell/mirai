import { Outlet, createFileRoute } from '@tanstack/react-router'

// Layout for /sources: the index renders the reports list, nested routes
// (e.g. $uploadId/review) render in place of it via this Outlet.
export const Route = createFileRoute('/sources')({
  component: () => <Outlet />,
})
