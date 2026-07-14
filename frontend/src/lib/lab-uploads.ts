import type { UploadStatus } from '@/client'

// Non-terminal statuses that keep the sources list and review page polling.
export const IN_PROGRESS: ReadonlySet<UploadStatus> = new Set(['pending', 'processing'])
