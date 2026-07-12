import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { listBiomarkersOptions } from '@/client/@tanstack/react-query.gen'
import type { BiomarkerSeries } from '@/client'
import { apiErrorMessage } from '@/lib/api'

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
  const biomarkers = useQuery(listBiomarkersOptions())

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Biomarkers</h1>
      <p className="text-muted-foreground">
        Track your biomarkers over time. Use “Add data” in the top bar to upload
        a blood-test PDF or enter values manually.
      </p>

      {biomarkers.isError ? (
        <p className="text-sm text-destructive">{apiErrorMessage(biomarkers.error)}</p>
      ) : biomarkers.data === undefined ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : biomarkers.data.length === 0 ? (
        <p className="text-sm text-muted-foreground">No biomarkers yet.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="py-2 font-medium">Biomarker</th>
              <th className="py-2 font-medium">Latest</th>
              <th className="py-2 font-medium">Reference</th>
              <th className="py-2 font-medium">History</th>
            </tr>
          </thead>
          <tbody>
            {biomarkers.data.map((b) => {
              const latest = b.measurements[b.measurements.length - 1]
              return (
                <tr key={b.slug} className="border-b">
                  <td className="py-2">{b.display_name}</td>
                  <td className="py-2 whitespace-nowrap">
                    <span className="font-mono">{latest.value}</span> {latest.unit}
                  </td>
                  <td className="py-2 text-muted-foreground">
                    {referenceRange(latest.reference_low, latest.reference_high)}
                  </td>
                  <td className="py-2 text-xs text-muted-foreground">{history(b)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
