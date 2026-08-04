import { z } from 'zod'

// Shared by the onboarding gate and /settings so the two can never drift.
export const profileSchema = z.object({
  sex: z.enum(['male', 'female'], { error: 'Select your biological sex.' }),
  dateOfBirth: z
    .date({ error: 'Enter your date of birth.' })
    .max(new Date(), { error: 'Date of birth cannot be in the future.' }),
})

export type ProfileFormValues = z.infer<typeof profileSchema>
