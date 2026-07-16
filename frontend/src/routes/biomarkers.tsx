import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Activity } from 'lucide-react'
import { listBiomarkerSeriesOptions } from '@/client/@tanstack/react-query.gen'
import type { BiomarkerSeries } from '@/client'
import { ApiErrorAlert } from '@/components/api-error-alert'
import { EmptyState } from '@/components/empty-state'
import { TableSkeleton } from '@/components/table-skeleton'
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
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Biomarkers</h1>
      <p className="text-muted-foreground">
        Track your biomarkers over time. Use “Add data” in the top bar to upload
        a blood-test PDF or enter values manually.
      </p>

      {biomarkers.isError ? (
        <ApiErrorAlert error={biomarkers.error} />
      ) : biomarkers.data === undefined ? (
        <TableSkeleton />
      ) : biomarkers.data.length === 0 ? (
        <EmptyState
          icon={<Activity />}
          title="No biomarkers yet"
          description="Your measurements will appear here once you add data."
        />
      ) : (
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
            {biomarkers.data.map((b) => {
              const latest = b.measurements[b.measurements.length - 1]
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
    </div>
  )
}
