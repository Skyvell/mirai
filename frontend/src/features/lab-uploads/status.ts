import type { ComponentProps } from 'react'
import type { UploadStatus } from '@/client'
import type { Badge } from '@/components/ui/badge'

// Non-terminal statuses that keep the sources list and review page polling.
export const IN_PROGRESS: ReadonlySet<UploadStatus> = new Set(['queued', 'processing'])

export const POLL_MS = 3000

// User-facing label per lifecycle state; queued and processing read the same.
export const STATUS_LABEL: Record<UploadStatus, string> = {
  queued: 'Processing',
  processing: 'Processing',
  awaiting_review: 'Ready to review',
  confirmed: 'Confirmed',
  failed: 'Failed',
}

export const STATUS_VARIANT: Record<UploadStatus, ComponentProps<typeof Badge>['variant']> = {
  queued: 'outline',
  processing: 'outline',
  awaiting_review: 'default',
  confirmed: 'secondary',
  failed: 'destructive',
}
