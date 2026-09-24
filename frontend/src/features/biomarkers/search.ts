import { z } from 'zod'
import { BIOMARKER_STATUSES } from '@/features/biomarkers/status'

export const biomarkerSearchSchema = z.object({
  query: z.string().optional().catch(undefined),
  status: z.enum(BIOMARKER_STATUSES).optional().catch(undefined)
})
