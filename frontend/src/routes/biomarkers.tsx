import { useRef, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useAuth } from '@clerk/react'
import { Button } from '@/components/ui/button'
import { uploadLabPdf, type LabUploadResult } from '@/lib/api'

export const Route = createFileRoute('/biomarkers')({
  component: BiomarkersComponent,
})

type Status = 'idle' | 'uploading' | 'success' | 'error'

function referenceRange(low: string | null, high: string | null): string {
  if (low !== null && high !== null) return `${low}–${high}`
  if (low !== null) return `≥ ${low}`
  if (high !== null) return `≤ ${high}`
  return '—'
}

function BiomarkersComponent() {
  const { getToken } = useAuth()
  const inputRef = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState<LabUploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    // Reset so re-selecting the same file fires onChange again.
    event.target.value = ''
    if (!file) return

    setStatus('uploading')
    setError(null)
    setResult(null)
    try {
      const token = await getToken()
      if (!token) throw new Error('Not authenticated.')
      const res = await uploadLabPdf(token, file)
      setResult(res)
      setStatus('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStatus('error')
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
        <Button
          onClick={() => inputRef.current?.click()}
          disabled={status === 'uploading'}
        >
          {status === 'uploading' ? 'Parsing report… (takes up to 30 s)' : 'Upload lab PDF'}
        </Button>
      </div>

      {status === 'error' && <p className="text-sm text-destructive">{error}</p>}

      {status === 'success' && result && (
        <div className="flex flex-col gap-4">
          {result.measured_at && (
            <p className="text-sm text-muted-foreground">
              Collected {result.measured_at}
            </p>
          )}
          {result.measurements.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="py-2 font-medium">Biomarker</th>
                  <th className="py-2 font-medium">Value</th>
                  <th className="py-2 font-medium">Unit</th>
                  <th className="py-2 font-medium">Reference</th>
                </tr>
              </thead>
              <tbody>
                {result.measurements.map((m) => (
                  <tr key={m.biomarker_slug} className="border-b">
                    <td className="py-2">{m.display_name}</td>
                    <td className="py-2 font-mono">{m.value}</td>
                    <td className="py-2">{m.unit}</td>
                    <td className="py-2 text-muted-foreground">
                      {referenceRange(m.reference_low, m.reference_high)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {result.skipped.length > 0 && (
            <div className="text-sm text-muted-foreground">
              <p className="font-medium">Skipped</p>
              <ul className="list-inside list-disc">
                {result.skipped.map((s, i) => (
                  <li key={`${s.name}-${i}`}>
                    {s.name} ({s.reason})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
