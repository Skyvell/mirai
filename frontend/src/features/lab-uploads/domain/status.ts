import type { UploadStatus } from '@/client'

// Non-terminal statuses that keep the sources list and review page polling.
export const LAB_UPLOAD_IN_PROGRESS: ReadonlySet<UploadStatus> = new Set(['queued', 'processing'])
