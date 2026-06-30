import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: OverviewComponent,
})

function OverviewComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Overview</h1>
      <p className="text-muted-foreground">
        Personal health summary, key changes since last test, risk signals,
        active interventions, and recommended follow-ups.
      </p>
    </div>
  )
}
