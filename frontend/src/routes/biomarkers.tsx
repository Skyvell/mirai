import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Activity } from 'lucide-react'
import { listBiomarkerSeriesOptions } from '@/client/@tanstack/react-query.gen'
import type { BiomarkerSeries } from '@/client'
import { EmptyState } from '@/components/empty-state'
import { Page } from '@/components/page'
import { QueryPane } from '@/components/query-pane'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export const Route = createFileRoute('/biomarkers')({
  component: BiomarkersComponent,
})

function referenceRange(low: string | null, high: string | null): string {
  if (low !== null && high !== null) return `${low}–${high}`
  if (low !== null) return `≥ ${low}`
  if (high !== null) return `≤ ${high}`
  return '—'
}

function history(series: BiomarkerSeries): string {
  return series.measurements
    .map((m) => (m.measured_at ? `${m.value} (${m.measured_at})` : m.value))
    .join(' → ')
}

function BiomarkersComponent() {
  const biomarkers = useQuery(listBiomarkerSeriesOptions())

  return (
    <Page
      title="Biomarkers"
      description="Track your biomarkers over time. Use “Add data” in the top bar to upload a blood-test PDF or enter values manually."
    >
      <QueryPane
        query={biomarkers}
        empty={
          <EmptyState
            icon={<Activity />}
            title="No biomarkers yet"
            description="Your measurements will appear here once you add data."
          />
        }
      >
        {(series) => (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Biomarker</TableHead>
                <TableHead>Latest</TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>History</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {series.map((b) => {
                const latest = b.measurements.at(-1)
                if (!latest) return null
                return (
                  <TableRow key={b.slug}>
                    <TableCell>{b.display_name}</TableCell>
                    <TableCell>
                      <span className="font-mono">{latest.value}</span> {latest.unit}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {referenceRange(latest.reference_low, latest.reference_high)}
                    </TableCell>
                    <TableCell className="text-xs whitespace-normal text-muted-foreground">
                      {history(b)}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}
      </QueryPane>
    </Page>
  )
}
