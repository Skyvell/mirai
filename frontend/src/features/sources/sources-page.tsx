import { Page } from '@/components/page'
import { ReportSection } from '@/features/lab-uploads/components/report-section'

// Fan-in page: it arranges sections contributed by the features that own each
// kind of source, and fetches nothing itself. Device connections join later.
export function SourcesPage() {
  return (
    <Page
      title="Sources"
      description="Where your data comes from: uploaded lab reports today; device connections and omics files later."
    >
      <ReportSection />
    </Page>
  )
}
