import type { QueryClient } from '@tanstack/react-query'
import { listLabUploadsQueryKey } from '@/client/@tanstack/react-query.gen'
import { invalidateBiomarkerSeries } from '@/features/biomarkers/api'

// A new upload changes only the report list; no measurements exist yet.
export function invalidateLabUploads(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
}

// Confirming a draft or deleting a report changes both the report list and the
// series it feeds, so this reaches into biomarkers rather than restating its key.
export function invalidateLabUploadsAndSeries(queryClient: QueryClient) {
  invalidateLabUploads(queryClient)
  invalidateBiomarkerSeries(queryClient)
}
