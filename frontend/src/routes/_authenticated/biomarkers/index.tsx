import { createFileRoute } from '@tanstack/react-router'
import { BiomarkersPage } from '@/features/biomarkers/pages/biomarkers-page'
import { biomarkerSearchSchema } from '@/features/biomarkers/search'

export const Route = createFileRoute('/_authenticated/biomarkers/')({
  validateSearch: biomarkerSearchSchema,
  component: BiomarkersPage,
})
