import { createFileRoute } from '@tanstack/react-router'
import { SourcesPage } from '@/features/sources/sources-page'

export const Route = createFileRoute('/_authenticated/sources/')({
  component: SourcesPage,
})
