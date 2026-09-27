import type { MeResponse } from '@/client'

// Which fields a usable profile needs, owned by this feature so the route that
// gates on it doesn't restate them. Deliberately free of zod and date-fns: the
// shell imports this on the path that gates every route, and `schema.ts` would
// drag its whole validation chunk along.
export function isProfileComplete(me: MeResponse): boolean {
  return me.sex != null && me.date_of_birth != null
}
