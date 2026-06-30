import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/insights')({
  component: InsightsComponent,
})

function InsightsComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Insights</h1>
      <p className="text-muted-foreground">
        Trends, correlations, outliers, risk flags, possible drivers of change,
        intervention response, and personalized recommendations.
      </p>
    </div>
  )
}
