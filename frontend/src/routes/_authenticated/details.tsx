import { createFileRoute } from '@tanstack/react-router'
import { DetailsPage } from '@/features/details'

export const Route = createFileRoute('/_authenticated/details')({
  component: DetailsPage,
})
