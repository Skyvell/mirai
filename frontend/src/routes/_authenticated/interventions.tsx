import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'

export const Route = createFileRoute('/_authenticated/interventions')({
  component: () => <Page title="Interventions" description="Track interventions with goal, hypothesis, dose, frequency, adherence, side effects, target biomarkers/physiology, and before/during/after comparison." />,
})
