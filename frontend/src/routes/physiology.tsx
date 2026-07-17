import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'

export const Route = createFileRoute('/physiology')({
  component: PhysiologyComponent,
})

function PhysiologyComponent() {
  return (
    <Page
      title="Physiology"
      description="Sleep, HRV, resting and continuous heart rate, activity, exercise load, recovery/readiness, body temperature, and respiratory rate."
    />
  )
}
