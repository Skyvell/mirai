import type { QueryClient } from '@tanstack/react-query'
import {
  listBiomarkerSeriesQueryKey,
  listBiomarkersOptions,
} from '@/client/@tanstack/react-query.gen'
import type { BiomarkerRead } from '@/client'

// Reseeded only by a migration, so a reload is soon enough; refetching costs a
// JWT verify plus a DB hit on a backend that scales to zero.
export function biomarkersOptions() {
  return { ...listBiomarkersOptions(), staleTime: Infinity }
}

export function findBiomarker(
  biomarkers: BiomarkerRead[] | undefined,
  slug: string,
): BiomarkerRead | undefined {
  return biomarkers?.find((biomarker) => biomarker.slug === slug)
}

export function invalidateBiomarkerSeries(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: listBiomarkerSeriesQueryKey() })
}
