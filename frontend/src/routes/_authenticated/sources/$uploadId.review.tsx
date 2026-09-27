import { createFileRoute } from '@tanstack/react-router'
import { LabUploadReviewPage } from '@/features/lab-uploads'

export const Route = createFileRoute('/_authenticated/sources/$uploadId/review')({
  component: LabUploadReviewPage,
})
