import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/physiology')({
  component: PhysiologyComponent,
})

function PhysiologyComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Physiology</h1>
      <p className="text-muted-foreground">
        Sleep, HRV, resting and continuous heart rate, activity, exercise load,
        recovery/readiness, body temperature, and respiratory rate.
      </p>
    </div>
  )
}
