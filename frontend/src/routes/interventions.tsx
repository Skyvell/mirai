import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'

export const Route = createFileRoute('/interventions')({
  component: InterventionsComponent,
})

function InterventionsComponent() {
  return (
    <Page
      title="Interventions"
      description="Track interventions with goal, hypothesis, dose, frequency, adherence, side effects, target biomarkers/physiology, and before/during/after comparison."
    />
  )
}
