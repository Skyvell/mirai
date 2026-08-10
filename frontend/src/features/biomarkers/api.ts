import type { QueryClient } from '@tanstack/react-query'
import {
  listBiomarkerSeriesQueryKey,
  listBiomarkersOptions,
} from '@/client/@tanstack/react-query.gen'

// Warmed by the app shell rather than by whatever opens the marker picker: the
// backend scales to zero, so this absorbs the cold start during page load.
export function prefetchBiomarkerCatalogue(queryClient: QueryClient) {
  return queryClient.prefetchQuery(listBiomarkersOptions())
}

// Every measurement write — manual entry, a confirmed lab draft, a deleted
// report — lands in the same series payload, so one helper states it once.
export function invalidateBiomarkerSeries(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: listBiomarkerSeriesQueryKey() })
}
