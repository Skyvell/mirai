import type { QueryClient } from '@tanstack/react-query'
import {
  listBiomarkerIntervalsOptions,
  listBiomarkerSeriesQueryKey,
  listBiomarkersOptions,
} from '@/client/@tanstack/react-query.gen'

// Reseeded only by a migration, so a reload is soon enough; refetching costs a
// JWT verify plus a DB hit on a backend that scales to zero.
export function biomarkersOptions() {
  return { ...listBiomarkersOptions(), staleTime: Infinity }
}

// Seeded by the same migration as the catalogue, so the same reasoning holds.
export function biomarkerIntervalsOptions() {
  return { ...listBiomarkerIntervalsOptions(), staleTime: Infinity }
}

export function invalidateBiomarkerSeries(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: listBiomarkerSeriesQueryKey() })
}
