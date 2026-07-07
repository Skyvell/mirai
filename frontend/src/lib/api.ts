const API_URL = import.meta.env.VITE_API_URL

/** Fetch the authenticated caller's identity from the backend, proving JWT verification. */
export async function getMe(token: string): Promise<{ user_id: string }> {
  const res = await fetch(`${API_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    throw new Error(`GET /me failed: ${res.status}`)
  }
  return res.json()
}

export interface Measurement {
  biomarker_slug: string
  display_name: string
  value: string
  unit: string
  reference_low: string | null
  reference_high: string | null
  measured_at: string | null
}

export interface SkippedMarker {
  name: string
  value: string
  unit: string | null
  reason: string
}

export interface LabUploadResult {
  upload_id: string
  filename: string
  status: string
  measured_at: string | null
  measurements: Measurement[]
  skipped: SkippedMarker[]
}

/** Upload a lab PDF for parsing. Sets no Content-Type so the browser adds the multipart boundary. */
export async function uploadLabPdf(token: string, file: File): Promise<LabUploadResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_URL}/lab-uploads`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.detail ?? `Upload failed: ${res.status}`)
  }
  return res.json()
}
