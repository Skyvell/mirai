import type { QueryClient } from '@tanstack/react-query'
import { listLabUploadsQueryKey } from '@/client/@tanstack/react-query.gen'
import type { LabUploadDetail, LabUploadSummary } from '@/client'
import { invalidateBiomarkerSeries } from '@/features/biomarkers/api'
import { IN_PROGRESS } from '@/features/lab-uploads/status'

const POLL_MS = 3000

// Parsing is asynchronous, so both the list and a single report poll while any
// row is non-terminal. The predicate lives here rather than at the two call
// sites so the interval and the terminal set can never disagree.
export function listPollInterval(uploads: LabUploadSummary[] | undefined) {
  return uploads?.some((upload) => IN_PROGRESS.has(upload.status)) ? POLL_MS : false
}

export function detailPollInterval(upload: LabUploadDetail | undefined) {
  return upload && IN_PROGRESS.has(upload.status) ? POLL_MS : false
}

// A new upload changes only the report list; no measurements exist yet.
export function invalidateLabUploads(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: listLabUploadsQueryKey() })
}

// Confirming a draft or deleting a report changes both the report list and the
// series it feeds, so this reaches into biomarkers rather than restating its key.
export function invalidateAfterLabWrite(queryClient: QueryClient) {
  invalidateLabUploads(queryClient)
  invalidateBiomarkerSeries(queryClient)
}
