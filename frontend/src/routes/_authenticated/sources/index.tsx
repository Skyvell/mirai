import { createFileRoute } from '@tanstack/react-router'
import { SourcesPage } from '@/features/sources'

export const Route = createFileRoute('/_authenticated/sources/')({
  component: SourcesPage,
})
