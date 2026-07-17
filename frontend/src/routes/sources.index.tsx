import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { ReportsList } from '@/components/reports-list'

export const Route = createFileRoute('/sources/')({
  component: SourcesComponent,
})

function SourcesComponent() {
  return (
    <Page
      title="Sources"
      description="Where your data comes from: uploaded lab reports today; device connections and omics files later."
    >
      <ReportsList />
    </Page>
  )
}
