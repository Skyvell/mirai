import { createFileRoute } from '@tanstack/react-router'
import { BiomarkersPage, biomarkerSearchSchema } from '@/features/biomarkers'

export const Route = createFileRoute('/_authenticated/biomarkers/')({
  validateSearch: biomarkerSearchSchema,
  component: BiomarkersPage,
})
