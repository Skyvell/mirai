import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/body')({
  component: BodyComponent,
})

function BodyComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Body</h1>
      <p className="text-muted-foreground">
        Weight, body fat, waist circumference, blood pressure, VO2 max, and grip
        strength.
      </p>
    </div>
  )
}
