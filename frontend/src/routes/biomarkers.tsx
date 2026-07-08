import { useCallback, useEffect, useRef, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useAuth } from '@clerk/react'
import { Button } from '@/components/ui/button'
import {
  getBiomarkers,
  uploadLabPdf,
  type BiomarkerSeries,
  type LabUploadResult,
} from '@/lib/api'

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
  const { getToken } = useAuth()
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<LabUploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [biomarkers, setBiomarkers] = useState<BiomarkerSeries[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  const loadBiomarkers = useCallback(async () => {
    const token = await getToken()
    if (!token) throw new Error('Not authenticated.')
    setBiomarkers(await getBiomarkers(token))
  }, [getToken])

  useEffect(() => {
    loadBiomarkers().catch((err) => setLoadError(String(err)))
  }, [loadBiomarkers])

  async function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    // Reset so re-selecting the same file fires onChange again.
    event.target.value = ''
    if (!file) return

    setUploading(true)
    setError(null)
    setResult(null)
    try {
      const token = await getToken()
      if (!token) throw new Error('Not authenticated.')
      setResult(await uploadLabPdf(token, file))
      await loadBiomarkers()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-semibold tracking-tight">Biomarkers</h1>
      <p className="text-muted-foreground">
        Upload a blood-test PDF to track your biomarkers over time.
      </p>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={onFileChange}
      />
      <div>
        <Button onClick={() => inputRef.current?.click()} disabled={uploading}>
          {uploading ? 'Parsing report… (takes up to 30 s)' : 'Upload lab PDF'}
        </Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {result && (result.measured_at !== null || result.skipped.length > 0) && (
        <div className="text-sm text-muted-foreground">
          {result.measured_at && <p>Parsed report collected {result.measured_at}.</p>}
          {result.skipped.length > 0 && (
            <>
              <p className="font-medium">Skipped</p>
              <ul className="list-inside list-disc">
                {result.skipped.map((s, i) => (
                  <li key={`${s.name}-${i}`}>
                    {s.name} ({s.reason})
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {loadError ? (
        <p className="text-sm text-destructive">{loadError}</p>
      ) : biomarkers === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : biomarkers.length === 0 ? (
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
            {biomarkers.map((b) => {
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
