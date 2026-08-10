import { createFileRoute } from '@tanstack/react-router'
import { ReviewPage } from '@/features/lab-uploads/review-page'

export const Route = createFileRoute('/_authenticated/sources/$uploadId/review')({
  component: ReviewRoute,
})

function ReviewRoute() {
  const { uploadId } = Route.useParams()
  return <ReviewPage uploadId={uploadId} />
}
