import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'
import { BiomarkersPage } from '@/features/biomarkers/pages/biomarkers-page'

const biomarkerSearchSchema = z.object({
  q: z.string().optional().catch(undefined),
})

export const Route = createFileRoute('/_authenticated/biomarkers/')({
  validateSearch: biomarkerSearchSchema,
  component: BiomarkersPage,
})
