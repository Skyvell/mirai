import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/reports')({
  component: ReportsComponent,
})

function ReportsComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Reports</h1>
      <p className="text-muted-foreground">
        Lab report history, biomarker trend reports, omics reports, intervention
        evaluation reports, and doctor/export reports.
      </p>
    </div>
  )
}
