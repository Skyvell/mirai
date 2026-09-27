import type { UploadStatus } from '@/client'

export const LAB_UPLOAD_IN_PROGRESS: ReadonlySet<UploadStatus> = new Set(['queued', 'processing'])
