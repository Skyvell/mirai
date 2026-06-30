import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/biomarkers')({
  component: BiomarkersComponent,
})

function BiomarkersComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Biomarkers</h1>
      <p className="text-muted-foreground">
        Blood markers, hormones, inflammation, metabolic, cardiovascular, liver,
        kidney, nutrient status, immune, and aging/longevity markers.
      </p>
    </div>
  )
}
