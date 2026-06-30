import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/lifestyle')({
  component: LifestyleComponent,
})

function LifestyleComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">
        Lifestyle &amp; Exposures
      </h1>
      <p className="text-muted-foreground">
        Nutrition, supplements, medications, exercise, sleep schedule, stress,
        alcohol, caffeine, nicotine, sunlight, illness/infection, and
        environmental exposures.
      </p>
    </div>
  )
}
