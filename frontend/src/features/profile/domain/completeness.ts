import type { MeResponse, Sex } from '@/client'

export type CompleteProfile = MeResponse & { sex: Sex; date_of_birth: string }

export function isProfileComplete(me: MeResponse): me is CompleteProfile {
  return me.sex != null && me.date_of_birth != null
}
