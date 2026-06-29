import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/about')({
  component: AboutComponent,
})

function AboutComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">About</h1>
      <p className="text-muted-foreground">
        Mirai is a precision-health app for individuals optimizing their own
        health, starting with blood biomarkers.
      </p>
    </div>
  )
}
