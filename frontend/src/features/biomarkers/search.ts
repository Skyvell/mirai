import { z } from 'zod'

export const biomarkerSearchSchema = z.object({
  q: z.string().optional().catch(undefined),
})
