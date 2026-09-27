import type { ComponentProps } from 'react'
import type { UploadStatus } from '@/client'
import type { Badge } from '@/components/ui/badge'

// User-facing label per lifecycle state; queued and processing read the same.
export const LAB_UPLOAD_STATUS_LABEL: Record<UploadStatus, string> = {
  queued: 'Processing',
  processing: 'Processing',
  awaiting_review: 'Ready to review',
  confirmed: 'Confirmed',
  failed: 'Failed',
}

export const LAB_UPLOAD_STATUS_VARIANT: Record<UploadStatus, ComponentProps<typeof Badge>['variant']> = {
  queued: 'outline',
  processing: 'outline',
  awaiting_review: 'default',
  confirmed: 'secondary',
  failed: 'destructive',
}
