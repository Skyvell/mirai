import { useQuery } from '@tanstack/react-query'
import { Activity } from 'lucide-react'
import { listBiomarkerSeriesOptions } from '@/client/@tanstack/react-query.gen'
import type { BiomarkerMeasurementPoint } from '@/client'
import { biomarkerCatalogueOptions, findBiomarker } from '@/features/biomarkers/api'
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

function referenceRange(low: string | null, high: string | null): string {
  if (low !== null && high !== null) return `${low}–${high}`
  if (low !== null) return `≥ ${low}`
  if (high !== null) return `≤ ${high}`
  return '—'
}

function history(measurements: BiomarkerMeasurementPoint[]): string {
  return measurements
    .map((m) => (m.measured_at ? `${m.value} (${m.measured_at})` : m.value))
    .join(' → ')
}

export function BiomarkersPage() {
  const series = useQuery(listBiomarkerSeriesOptions())

  // Catalogue is the single source of truth for display names, joined by slug.
  const catalogue = useQuery(biomarkerCatalogueOptions())

  return (
    <Page
      title="Biomarkers"
      description="Track your biomarkers over time. Use “Add data” in the top bar to upload a blood-test PDF or enter values manually."
    >
      <QueryPane
        query={series}
        empty={
          <EmptyState
            icon={<Activity />}
            title="No biomarkers yet"
            description="Your measurements will appear here once you add data."
          />
        }
      >
        {(seriesBySlug) => (
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
              {Object.entries(seriesBySlug).map(([slug, measurements]) => {
                const latest = measurements.at(-1)
                if (!latest) return null
                return (
                  <TableRow key={slug}>
                    <TableCell>{findBiomarker(catalogue.data, slug)?.display_name ?? slug}</TableCell>
                    <TableCell>
                      <span className="font-mono">{latest.value}</span> {latest.unit}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {referenceRange(latest.reference_low, latest.reference_high)}
                    </TableCell>
                    <TableCell className="text-xs whitespace-normal text-muted-foreground">
                      {history(measurements)}
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
