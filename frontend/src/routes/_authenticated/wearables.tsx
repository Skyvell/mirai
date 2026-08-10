import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'

export const Route = createFileRoute('/_authenticated/wearables')({
  component: WearablesComponent,
})

function WearablesComponent() {
  return (
    <Page
      title="Wearables"
      description="Sleep, HRV, resting and continuous heart rate, activity, exercise load, recovery/readiness, body temperature, and respiratory rate."
    />
  )
}
