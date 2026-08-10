import { parse } from 'date-fns'
import { z } from 'zod'

import type { Sex } from '@/client'

// Runtime literals for zod; `satisfies` ties them to the generated Sex type, so a
// backend rename or removal of a value fails the frontend build.
const SEX_VALUES = ['male', 'female'] as const satisfies readonly Sex[]

// Shared by the onboarding gate and /settings so the two can never drift.
export const profileSchema = z.object({
  sex: z.enum(SEX_VALUES, { error: 'Select your biological sex.' }),
  dateOfBirth: z
    .date({ error: 'Enter your date of birth.' })
    .max(new Date(), { error: 'Date of birth cannot be in the future.' }),
})

export type ProfileFormValues = z.infer<typeof profileSchema>

// The API sends YYYY-MM-DD; parse to local midnight, since `new Date(str)` reads
// it as UTC and can shift a day in negative offsets.
export function parseDateOfBirth(value: string | null | undefined): Date | undefined {
  return value ? parse(value, 'yyyy-MM-dd', new Date()) : undefined
}

