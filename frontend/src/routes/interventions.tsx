import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/interventions')({
  component: InterventionsComponent,
})

function InterventionsComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Interventions</h1>
      <p className="text-muted-foreground">
        Track interventions with goal, hypothesis, dose, frequency, adherence,
        side effects, target biomarkers/physiology, and before/during/after
        comparison.
      </p>
    </div>
  )
}
