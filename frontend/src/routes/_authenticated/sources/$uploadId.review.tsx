import { createFileRoute } from '@tanstack/react-router'
import { LabUploadReviewPage } from '@/features/lab-uploads'

export const Route = createFileRoute('/_authenticated/sources/$uploadId/review')({
  component: ReviewRoute,
})

function ReviewRoute() {
  const { uploadId } = Route.useParams()
  return <LabUploadReviewPage uploadId={uploadId} />
}
