import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'

export const Route = createFileRoute('/insights')({
  component: InsightsComponent,
})

function InsightsComponent() {
  return (
    <Page
      title="Insights"
      description="Trends, correlations, outliers, risk flags, possible drivers of change, intervention response, and personalized recommendations."
    />
  )
}
