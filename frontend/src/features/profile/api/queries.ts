import type { QueryClient } from '@tanstack/react-query'
import type { MeResponse } from '@/client'
import { currentUserQueryKey } from '@/client/@tanstack/react-query.gen'

// A PATCH response is the authoritative MeResponse, so seeding the cache with it
// flips the onboarding gate without a redundant refetch.
export function seedProfileCache(queryClient: QueryClient, profile: MeResponse) {
  queryClient.setQueryData(currentUserQueryKey(), profile)
}
