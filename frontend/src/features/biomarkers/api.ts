import type { QueryClient } from '@tanstack/react-query'
import { listBiomarkerSeriesQueryKey } from '@/client/@tanstack/react-query.gen'

// Every measurement write — manual entry, a confirmed lab draft, a deleted
// report — lands in the same series payload, so one helper states it once.
export function invalidateBiomarkerSeries(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: listBiomarkerSeriesQueryKey() })
}
