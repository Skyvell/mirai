import { createFileRoute } from '@tanstack/react-router'
import { BiomarkersPage } from '@/features/biomarkers/pages/biomarkers-page'

export const Route = createFileRoute('/_authenticated/biomarkers/')({
  component: BiomarkersPage,
})
