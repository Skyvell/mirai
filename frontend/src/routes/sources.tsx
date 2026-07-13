import { createFileRoute } from '@tanstack/react-router'
import { ReportsList } from '@/components/reports-list'

export const Route = createFileRoute('/sources')({
  component: SourcesComponent,
})

function SourcesComponent() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Sources</h1>
      <p className="text-muted-foreground">
        Where your data comes from: uploaded lab reports today; device
        connections and omics files later.
      </p>

      <ReportsList />
    </div>
  )
}
